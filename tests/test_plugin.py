#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/test_plugin.py —— ddd-agent-plugin 单元测试（03-design §10）

UT-1 generate 幂等：两次生成产物逐字节一致
UT-2 drift 检出：篡改镜像后 drift_check 非零
UT-3 install/uninstall 可逆：卸载后宿主目录与安装前快照一致（AC-5）
UT-4 包内无 kb：生成产物与单一源均不含 kb/ 内容（AC-4）

运行：python -m unittest discover tests（纯标准库）
"""
import filecmp
import json
import os
import re
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
import drift_check
import generate
import install
import uninstall

ROOT = generate.ROOT


def _generate_once(host, out):
    manifest = generate.load_manifest()
    generate.generate_host(manifest, host, out)
    return manifest


class TestGenerate(unittest.TestCase):
    """UT-1 generate 幂等 + UT-4 无 kb"""

    def test_generate_idempotent(self):
        with tempfile.TemporaryDirectory() as d1, tempfile.TemporaryDirectory() as d2:
            _generate_once("reasonix", d1)
            _generate_once("reasonix", d2)
            cmp = filecmp.dircmp(
                os.path.join(d1, "reasonix"), os.path.join(d2, "reasonix"))
            self.assertEqual(cmp.left_only, [])
            self.assertEqual(cmp.right_only, [])
            self.assertEqual(cmp.diff_files, [])
            # 递归校验
            diffs = drift_check.compare_trees(
                os.path.join(d1, "reasonix"), os.path.join(d2, "reasonix"))
            self.assertEqual(diffs, [])

    def test_generate_both_hosts(self):
        with tempfile.TemporaryDirectory() as d:
            for host, sub in (("reasonix", ".reasonix"), ("claude", ".claude")):
                _generate_once(host, d)
                base = os.path.join(d, host)
                self.assertTrue(os.path.isdir(base))
                skills = os.listdir(os.path.join(base, sub, "skills"))
                # 13 个 skill 目录（bootstrap + 5 角色 + 7 纪律）
                self.assertEqual(len(skills), 13)

    def test_rendered_frontmatter(self):
        with tempfile.TemporaryDirectory() as d:
            _generate_once("claude", d)
            with open(os.path.join(
                    d, "claude", ".claude", "skills", "doc-driven", "SKILL.md"),
                    encoding="utf-8") as f:
                head = f.read(200)
            self.assertIn("name: doc-driven", head)   # 占位符已渲染
            self.assertNotIn("{{SKILL_NAME}}", head)  # 无残留占位符

    def test_no_kb_in_output(self):
        """UT-4 包内无 kb：生成产物不含 kb/ 路径或内容。"""
        with tempfile.TemporaryDirectory() as d:
            for host in ("reasonix", "claude"):
                _generate_once(host, d)
                for dirpath, dirnames, filenames in os.walk(os.path.join(d, host)):
                    self.assertNotIn("kb", [x.lower() for x in dirnames])
                    self.assertNotIn("/kb/", dirpath.replace("\\", "/").lower())


class TestDrift(unittest.TestCase):
    """UT-2 drift 检出"""

    def test_clean_then_drift(self):
        with tempfile.TemporaryDirectory() as d:
            _generate_once("reasonix", d)
            base = os.path.join(d, "reasonix")
            # 篡改
            target = os.path.join(base, ".reasonix", "skills", "gate", "SKILL.md")
            with open(target, "a", encoding="utf-8") as f:
                f.write("\ntampered\n")
            diffs = drift_check.check_host(
                generate.load_manifest(), "reasonix", d)
            self.assertTrue(any("gate" in x for x in diffs),
                            f"应检出 gate 漂移，实际: {diffs}")

    def test_missing_mirror(self):
        with tempfile.TemporaryDirectory() as d:
            diffs = drift_check.check_host(generate.load_manifest(), "claude", d)
            self.assertTrue(any("missing" in x for x in diffs))


class TestInstallUninstall(unittest.TestCase):
    """UT-3 install/uninstall 可逆（AC-5）"""

    def _make_host(self, tmp):
        """构造宿主：预置一个与插件同名的既有 skill（验证覆盖+恢复）。"""
        host_root = os.path.join(tmp, "host")
        pre = os.path.join(host_root, ".reasonix", "skills", "doc-driven")
        os.makedirs(pre, exist_ok=True)
        with open(os.path.join(pre, "SKILL.md"), "w", encoding="utf-8") as f:
            f.write("USER ORIGINAL")
        return host_root

    def test_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            host_root = self._make_host(tmp)
            # 安装（main 以 sys.exit(0) 收尾）
            with self.assertRaises(SystemExit) as ictx:
                install.main(["--host", "reasonix", "--target", host_root])
            self.assertEqual(ictx.exception.code, 0)
            # 覆盖生效
            with open(os.path.join(
                    host_root, ".reasonix", "skills", "doc-driven", "SKILL.md"),
                    encoding="utf-8") as f:
                self.assertIn("doc-driven", f.read(200))
            # 卸载
            with self.assertRaises(SystemExit) as uctx:
                uninstall.main(["--host", "reasonix", "--target", host_root])
            self.assertEqual(uctx.exception.code, 0)
            # 原文件恢复
            with open(os.path.join(
                    host_root, ".reasonix", "skills", "doc-driven", "SKILL.md"),
                    encoding="utf-8") as f:
                self.assertEqual(f.read(), "USER ORIGINAL")
            # 插件文件已清空（6 skill + scripts 全部移除）
            skills = os.listdir(os.path.join(host_root, ".reasonix", "skills"))
            self.assertEqual(skills, ["doc-driven"])

    def test_uninstall_without_manifest_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            host_root = self._make_host(tmp)
            # 无 manifest → 拒绝卸载
            with self.assertRaises(SystemExit) as ctx:
                uninstall.main(["--host", "reasonix", "--target", host_root])
            self.assertEqual(ctx.exception.code, 1)


class TestManifest(unittest.TestCase):
    """manifest 解析与 schema 完整性"""

    def test_manifest_schema(self):
        manifest = generate.load_manifest()
        self.assertEqual(manifest["id"], "ddd-agent-plugin")
        self.assertEqual(len(manifest["skills"]), 13)
        ids = [s["id"] for s in manifest["skills"]]
        self.assertEqual(
            sorted(ids),
            ["architect", "bootstrap", "debug", "doc-driven", "gate",
             "goal-creator", "memory-protocol", "no-fake-test", "pm",
             "product-manager", "review", "ui-designer", "verify"])
        self.assertIn("reasonix", manifest["hosts"])
        self.assertIn("claude", manifest["hosts"])
        self.assertEqual(manifest["hosts"]["reasonix"]["status"], "verified")
        # 模板文件齐全
        for sid in ids:
            self.assertTrue(os.path.isfile(
                os.path.join(ROOT, "templates", sid + ".md")),
                f"缺模板 templates/{sid}.md")


class TestScaffold(unittest.TestCase):
    """UT-5 scaffold 骨架生成（FR-014/AC-8 支撑）"""

    def test_scaffold_creates_five_docs(self):
        import scaffold
        with tempfile.TemporaryDirectory() as tmp:
            created, skipped = scaffold.scaffold(tmp)
            self.assertEqual(len(created), 5)
            self.assertEqual(len(skipped), 0)
            for name in ("00-vision", "01-requirements", "02-architecture",
                         "03-design", "04-tasks"):
                self.assertTrue(os.path.isfile(
                    os.path.join(tmp, "docs", name + ".md")))
            # frontmatter 合法（含 status: draft）
            with open(os.path.join(tmp, "docs", "00-vision.md"),
                      encoding="utf-8") as f:
                self.assertIn("status: draft", f.read(120))

    def test_scaffold_idempotent(self):
        import scaffold
        with tempfile.TemporaryDirectory() as tmp:
            scaffold.scaffold(tmp)
            created, skipped = scaffold.scaffold(tmp)
            self.assertEqual(len(created), 0)
            self.assertEqual(len(skipped), 5)


class TestReferences(unittest.TestCase):
    """UT-6 references 打包 + 角色 skill 引用闭环（FR-015/AC-9）"""

    def test_references_in_mirror(self):
        with tempfile.TemporaryDirectory() as d:
            _generate_once("reasonix", d)
            refs = os.listdir(os.path.join(d, "reasonix", "references"))
            self.assertIn("adversarial-selection.md", refs)
            self.assertIn("pm-thinking-guide.md", refs)
            self.assertIn("code-review-standard.md", refs)
            self.assertIn("doc-driven-dev.md", refs)
            self.assertIn("capability-registry.md", refs)

    def test_role_skill_refs_resolve(self):
        """角色 skill 内 `references/X.md` 引用在镜像中可达（闭环）。"""
        with tempfile.TemporaryDirectory() as d:
            for host, sub in (("reasonix", ".reasonix"), ("claude", ".claude")):
                _generate_once(host, d)
                base = os.path.join(d, host)
                for role in ("product-manager", "architect"):
                    sp = os.path.join(base, sub, "skills", role, "SKILL.md")
                    with open(sp, encoding="utf-8") as f:
                        content = f.read()
                    for m in re.findall(r"references/([\w\-\.]+)", content):
                        self.assertTrue(
                            os.path.isfile(os.path.join(base, "references", m)),
                            f"{host}/{role} 引用 references/{m} 但文件缺失")


class TestMultiHostRoundtrip(unittest.TestCase):
    """回归：多宿主 install 的 backup 互相覆盖（v0.2.0 真机发现）
    场景：同 target 装 reasonix + claude → 依次卸载 → 宿主文件全部恢复。"""

    def _make_host(self, tmp):
        host_root = os.path.join(tmp, "host")
        # reasonix 既有 skill
        r = os.path.join(host_root, ".reasonix", "skills", "doc-driven")
        os.makedirs(r, exist_ok=True)
        with open(os.path.join(r, "SKILL.md"), "w", encoding="utf-8") as f:
            f.write("R-ORIGINAL")
        # claude 既有 skill
        c = os.path.join(host_root, ".claude", "skills", "doc-driven")
        os.makedirs(c, exist_ok=True)
        with open(os.path.join(c, "SKILL.md"), "w", encoding="utf-8") as f:
            f.write("C-ORIGINAL")
        # 宿主已有 ddd_gate.py（模拟项目自带机械闸）
        sdir = os.path.join(host_root, "scripts")
        os.makedirs(sdir, exist_ok=True)
        with open(os.path.join(sdir, "ddd_gate.py"), "w", encoding="utf-8") as f:
            f.write("# HOST GATE VERSION")
        return host_root

    def test_multi_host_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            host_root = self._make_host(tmp)
            for host in ("reasonix", "claude"):
                with self.assertRaises(SystemExit) as ctx:
                    install.main(["--host", host, "--target", host_root])
                self.assertEqual(ctx.exception.code, 0)
            # 后装的 claude 不应破坏 reasonix 的备份目录
            self.assertTrue(os.path.isdir(os.path.join(
                host_root, install.backup_dir_name("reasonix"))))
            self.assertTrue(os.path.isdir(os.path.join(
                host_root, install.backup_dir_name("claude"))))
            # 依次卸载
            for host in ("claude", "reasonix"):
                with self.assertRaises(SystemExit) as ctx:
                    uninstall.main(["--host", host, "--target", host_root])
                self.assertEqual(ctx.exception.code, 0)
            # 全部恢复
            with open(os.path.join(host_root, ".reasonix", "skills",
                                   "doc-driven", "SKILL.md"), encoding="utf-8") as f:
                self.assertEqual(f.read(), "R-ORIGINAL")
            with open(os.path.join(host_root, ".claude", "skills",
                                   "doc-driven", "SKILL.md"), encoding="utf-8") as f:
                self.assertEqual(f.read(), "C-ORIGINAL")
            with open(os.path.join(host_root, "scripts", "ddd_gate.py"),
                      encoding="utf-8") as f:
                self.assertEqual(f.read(), "# HOST GATE VERSION")
            # 零残留：宿主只保留原有文件（插件 skill 全部清除）
            self.assertEqual(
                os.listdir(os.path.join(host_root, ".reasonix", "skills")),
                ["doc-driven"])
            self.assertEqual(
                os.listdir(os.path.join(host_root, ".claude", "skills")),
                ["doc-driven"])
            self.assertEqual(os.listdir(os.path.join(host_root, "scripts")),
                             ["ddd_gate.py"])
            self.assertEqual(
                [x for x in os.listdir(host_root)
                 if x.startswith(".ddd-agent-plugin")], [])


class TestHooks(unittest.TestCase):
    """hooks 自动挂载：合并保留原 hooks / 无 settings 时创建删除（AC-5 扩展）"""

    def test_merge_keeps_existing_hooks(self):
        with tempfile.TemporaryDirectory() as tmp:
            host_root = os.path.join(tmp, "host")
            os.makedirs(os.path.join(host_root, ".reasonix"))
            orig = {"hooks": {"PreToolUse": [
                {"matcher": "Bash",
                 "hooks": [{"type": "command", "command": "echo hi"}]}]}}
            sp = os.path.join(host_root, ".reasonix", "settings.json")
            with open(sp, "w", encoding="utf-8") as f:
                json.dump(orig, f)
            with self.assertRaises(SystemExit):
                install.main(["--host", "reasonix", "--target", host_root])
            with open(sp, encoding="utf-8") as f:
                merged = json.load(f)
            matchers = [e["matcher"] for e in merged["hooks"]["PreToolUse"]]
            self.assertIn("Bash", matchers)                      # 原 hook 保留
            self.assertIn("Edit|Write|NotebookEdit", matchers)   # 插件 hook 追加
            # 卸载后恢复原状
            with self.assertRaises(SystemExit):
                uninstall.main(["--host", "reasonix", "--target", host_root])
            with open(sp, encoding="utf-8") as f:
                self.assertEqual(json.load(f), orig)

    def test_create_and_remove_settings(self):
        with tempfile.TemporaryDirectory() as tmp:
            host_root = os.path.join(tmp, "host")
            os.makedirs(os.path.join(host_root, ".reasonix"))
            sp = os.path.join(host_root, ".reasonix", "settings.json")
            with self.assertRaises(SystemExit):
                install.main(["--host", "reasonix", "--target", host_root])
            self.assertTrue(os.path.isfile(sp))
            with open(sp, encoding="utf-8") as f:
                self.assertIn("Edit|Write|NotebookEdit",
                              json.dumps(json.load(f)))
            with self.assertRaises(SystemExit):
                uninstall.main(["--host", "reasonix", "--target", host_root])
            self.assertFalse(os.path.isfile(sp))  # 原本不存在 → 删除


if __name__ == "__main__":
    unittest.main()
