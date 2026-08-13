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
                # 6 个 skill 目录
                self.assertEqual(len(skills), 6)

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
        self.assertEqual(len(manifest["skills"]), 6)
        ids = [s["id"] for s in manifest["skills"]]
        self.assertEqual(
            sorted(ids),
            ["doc-driven", "gate", "memory-protocol",
             "no-fake-test", "review", "verify"])
        self.assertIn("reasonix", manifest["hosts"])
        self.assertIn("claude", manifest["hosts"])
        self.assertEqual(manifest["hosts"]["reasonix"]["status"], "verified")
        # 模板文件齐全
        for sid in ids:
            self.assertTrue(os.path.isfile(
                os.path.join(ROOT, "templates", sid + ".md")),
                f"缺模板 templates/{sid}.md")


if __name__ == "__main__":
    unittest.main()
