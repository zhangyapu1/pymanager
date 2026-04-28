"""
github_api.py 单元测试
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.github_api import (
    PROJECT_URL,
    REPO_OWNER,
    REPO_NAME,
    DOWNLOAD_TIMEOUT,
    USE_WEBDAV_FOR_UPDATES,
    WEBDAV_URL,
    is_version_greater,
)


class TestGithubApiConstants:
    def test_project_url_format(self):
        """测试项目 URL 格式"""
        assert PROJECT_URL.startswith("https://github.com/")
        assert "/" in PROJECT_URL

    def test_repo_owner_format(self):
        """测试仓库所有者格式"""
        assert isinstance(REPO_OWNER, str)
        assert len(REPO_OWNER) > 0
        assert " " not in REPO_OWNER

    def test_repo_name_format(self):
        """测试仓库名称格式"""
        assert isinstance(REPO_NAME, str)
        assert len(REPO_NAME) > 0
        assert " " not in REPO_NAME

    def test_download_timeout_reasonable(self):
        """测试下载超时时间合理"""
        assert DOWNLOAD_TIMEOUT >= 10, "超时时间应 >= 10 秒"
        assert DOWNLOAD_TIMEOUT <= 300, "超时时间应 <= 300 秒"

    def test_webdav_enabled(self):
        """测试 WebDAV 更新默认启用"""
        assert USE_WEBDAV_FOR_UPDATES is True

    def test_webdav_url_format(self):
        """测试 WebDAV URL 格式"""
        assert WEBDAV_URL.startswith("https://")
        assert WEBDAV_URL.endswith("/")


class TestVersionComparison:
    def test_version_greater_major(self):
        """测试主版本号比较"""
        assert is_version_greater("2.0.0", "1.9.9")
        assert is_version_greater("1.0.0", "0.9.9")
        assert not is_version_greater("1.0.0", "2.0.0")

    def test_version_greater_minor(self):
        """测试次版本号比较"""
        assert is_version_greater("1.2.0", "1.1.9")
        assert is_version_greater("1.1.0", "1.0.9")
        assert not is_version_greater("1.1.0", "1.2.0")

    def test_version_greater_patch(self):
        """测试补丁版本号比较"""
        assert is_version_greater("1.1.2", "1.1.1")
        assert not is_version_greater("1.1.1", "1.1.2")

    def test_version_greater_equal(self):
        """测试相等版本"""
        assert not is_version_greater("1.0.0", "1.0.0")
        assert not is_version_greater("2.0.0", "2.0.0")

    def test_version_greater_with_v_prefix(self):
        """测试带 v 前缀的版本号"""
        assert is_version_greater("v2.0.0", "v1.0.0")
        assert is_version_greater("v1.5.0", "v1.0.0")
        assert is_version_greater("v1.0.1", "v1.0.0")
        assert not is_version_greater("v1.0.0", "v1.0.0")

    def test_version_greater_real_world(self):
        """测试实际版本号"""
        assert is_version_greater("1.8.10", "1.8.9")
        assert is_version_greater("1.9.0", "1.8.10")
        assert is_version_greater("2.0.0", "1.99.99")


class TestWebdavCredentials:
    def test_webdav_credentials_function_exists(self):
        """测试 WebDAV 凭据函数存在"""
        from modules.github_api import _get_webdav_credentials
        assert callable(_get_webdav_credentials)

    def test_webdav_auth_function_exists(self):
        """测试 WebDAV 认证函数存在"""
        from modules.github_api import _build_webdav_auth
        assert callable(_build_webdav_auth)

    def test_webdav_auth_builds_correctly(self):
        """测试 WebDAV 认证头构建"""
        from modules.github_api import _build_webdav_auth
        auth = _build_webdav_auth("user", "pass")
        assert auth is not None
        assert auth.startswith("Basic ")
        import base64
        decoded = base64.b64decode(auth.split(" ")[1]).decode()
        assert decoded == "user:pass"

    def test_webdav_auth_empty_credentials(self):
        """测试空凭据返回 None"""
        from modules.github_api import _build_webdav_auth
        assert _build_webdav_auth("", "pass") is None
        assert _build_webdav_auth("user", "") is None
        assert _build_webdav_auth("", "") is None
