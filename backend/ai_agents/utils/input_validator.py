"""
输入验证工具模块

提供输入验证、恶意输入检测和输入清洗功能。
"""
import re
import logging
import html
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from urllib.parse import urlparse, quote

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """
    验证结果数据类

    Attributes:
        is_valid: 是否验证通过
        sanitized_value: 清洗后的值
        error_message: 错误信息
        warnings: 警告信息列表
        detected_threats: 检测到的威胁类型列表
    """
    is_valid: bool
    sanitized_value: Optional[str] = None
    error_message: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    detected_threats: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "is_valid": self.is_valid,
            "sanitized_value": self.sanitized_value,
            "error_message": self.error_message,
            "warnings": self.warnings,
            "detected_threats": self.detected_threats
        }


class InputValidator:
    """
    输入验证器

    提供目标格式验证、恶意输入检测和输入清洗功能。
    支持URL、IP地址、域名等格式的验证，以及SQL注入、XSS、命令注入等威胁检测。
    """

    URL_PATTERN = re.compile(
        r'^https?://'
        r'(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)*'
        r'[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?'
        r'(?::\d+)?'
        r'(?:/[^\s]*)?$',
        re.IGNORECASE
    )

    IPV4_PATTERN = re.compile(
        r'^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}'
        r'(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
    )

    IPV6_PATTERN = re.compile(
        r'^('
        r'([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}|'
        r'([0-9a-fA-F]{1,4}:){1,7}:|'
        r'([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|'
        r'([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|'
        r'([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|'
        r'([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|'
        r'([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|'
        r'[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|'
        r':((:[0-9a-fA-F]{1,4}){1,7}|:)|'
        r'fe80:(:[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]+|'
        r'::(ffff(:0{1,4})?:)?((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)|'
        r'([0-9a-fA-F]{1,4}:){1,4}:((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)'
        r')$',
        re.IGNORECASE
    )

    DOMAIN_PATTERN = re.compile(
        r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)*'
        r'[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$',
        re.IGNORECASE
    )

    SQL_INJECTION_PATTERNS = [
        re.compile(r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|TRUNCATE)\b)", re.IGNORECASE),
        re.compile(r"(\b(UNION|JOIN)\b.*\b(SELECT|FROM)\b)", re.IGNORECASE),
        re.compile(r"(--|\#|\/\*|\*\/)", re.IGNORECASE),
        re.compile(r"(\b(OR|AND)\b\s+['\"]?\d+['\"]?\s*=\s*['\"]?\d+['\"]?)", re.IGNORECASE),
        re.compile(r"(;\s*$|;\s*--)", re.IGNORECASE),
        re.compile(r"(\bEXEC\b|\bEXECUTE\b)", re.IGNORECASE),
        re.compile(r"(xp_cmdshell|sp_executesql)", re.IGNORECASE),
        re.compile(r"(CONCAT|CHAR|NCHAR|VARCHAR|NVARCHAR)\s*\(", re.IGNORECASE),
        re.compile(r"(WAITFOR\s+DELAY|BENCHMARK\s*\()", re.IGNORECASE),
        re.compile(r"('\s*(OR|AND)\s+')", re.IGNORECASE),
    ]

    XSS_PATTERNS = [
        re.compile(r"<\s*script[^>]*>", re.IGNORECASE),
        re.compile(r"<\s*/\s*script\s*>", re.IGNORECASE),
        re.compile(r"javascript\s*:", re.IGNORECASE),
        re.compile(r"on\w+\s*=", re.IGNORECASE),
        re.compile(r"<\s*iframe[^>]*>", re.IGNORECASE),
        re.compile(r"<\s*img[^>]+onerror\s*=", re.IGNORECASE),
        re.compile(r"<\s*svg[^>]*onload\s*=", re.IGNORECASE),
        re.compile(r"<\s*body[^>]*onload\s*=", re.IGNORECASE),
        re.compile(r"expression\s*\(", re.IGNORECASE),
        re.compile(r"<\s*embed[^>]*>", re.IGNORECASE),
        re.compile(r"<\s*object[^>]*>", re.IGNORECASE),
        re.compile(r"data\s*:\s*text/html", re.IGNORECASE),
        re.compile(r"vbscript\s*:", re.IGNORECASE),
    ]

    COMMAND_INJECTION_PATTERNS = [
        re.compile(r"[;&|`$]"),
        re.compile(r"\$\([^)]+\)"),
        re.compile(r"`[^`]+`"),
        re.compile(r"\|\s*\w+"),
        re.compile(r">\s*/"),
        re.compile(r"<\s*/"),
        re.compile(r"\b(cat|ls|pwd|whoami|id|uname|wget|curl|nc|netcat|bash|sh|cmd|powershell)\b", re.IGNORECASE),
        re.compile(r"\b(eval|exec|system|passthru|shell_exec)\s*\(", re.IGNORECASE),
        re.compile(r"\$\{[^}]+\}"),
        re.compile(r"%0[aAdD]", re.IGNORECASE),
    ]

    PATH_TRAVERSAL_PATTERNS = [
        re.compile(r"\.\./"),
        re.compile(r"\.\.\\"),
        re.compile(r"%2e%2e[/\\%]", re.IGNORECASE),
        re.compile(r"\.\.%2f", re.IGNORECASE),
        re.compile(r"\.\.%5c", re.IGNORECASE),
        re.compile(r"%252e%252e", re.IGNORECASE),
        re.compile(r"\.\.\/\.\.\/"),
        re.compile(r"\/etc\/passwd", re.IGNORECASE),
        re.compile(r"\/etc\/shadow", re.IGNORECASE),
        re.compile(r"c:\\windows", re.IGNORECASE),
        re.compile(r"c:/windows", re.IGNORECASE),
    ]

    DANGEROUS_CHARS = {
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#x27;',
        '/': '&#x2F;',
        '\\': '&#x5C;',
        '`': '&#x60;',
        '=': '&#x3D;',
    }

    def __init__(
        self,
        strict_mode: bool = True,
        enable_sanitization: bool = True,
        max_length: int = 2048
    ):
        """
        初始化输入验证器

        Args:
            strict_mode: 是否启用严格模式（严格模式下检测到威胁将验证失败）
            enable_sanitization: 是否启用输入清洗
            max_length: 最大输入长度限制
        """
        self.strict_mode = strict_mode
        self.enable_sanitization = enable_sanitization
        self.max_length = max_length

    def validate_url(self, url: str) -> ValidationResult:
        """
        验证URL格式

        Args:
            url: 待验证的URL字符串

        Returns:
            ValidationResult: 验证结果对象
        """
        if not url or not isinstance(url, str):
            return ValidationResult(
                is_valid=False,
                error_message="URL不能为空且必须为字符串类型"
            )

        url = url.strip()

        if len(url) > self.max_length:
            return ValidationResult(
                is_valid=False,
                error_message=f"URL长度超过限制（最大{self.max_length}字符）"
            )

        threats = self._detect_all_threats(url)
        sanitized = self._sanitize(url) if self.enable_sanitization else url

        if not self.URL_PATTERN.match(url):
            try:
                parsed = urlparse(url)
                if parsed.scheme not in ('http', 'https'):
                    return ValidationResult(
                        is_valid=False,
                        sanitized_value=sanitized,
                        error_message="URL必须以http://或https://开头",
                        detected_threats=threats
                    )
                if not parsed.netloc:
                    return ValidationResult(
                        is_valid=False,
                        sanitized_value=sanitized,
                        error_message="URL格式无效：缺少主机名",
                        detected_threats=threats
                    )
            except Exception as e:
                return ValidationResult(
                    is_valid=False,
                    sanitized_value=sanitized,
                    error_message=f"URL解析失败：{str(e)}",
                    detected_threats=threats
                )

        if threats and self.strict_mode:
            return ValidationResult(
                is_valid=False,
                sanitized_value=sanitized,
                error_message=f"检测到潜在威胁：{', '.join(threats)}",
                detected_threats=threats
            )

        warnings = []
        if threats and not self.strict_mode:
            warnings.append(f"检测到潜在威胁但已通过验证：{', '.join(threats)}")

        return ValidationResult(
            is_valid=True,
            sanitized_value=sanitized,
            warnings=warnings,
            detected_threats=threats
        )

    def validate_ip(self, ip: str, allow_ipv6: bool = True) -> ValidationResult:
        """
        验证IP地址格式

        Args:
            ip: 待验证的IP地址字符串
            allow_ipv6: 是否允许IPv6地址

        Returns:
            ValidationResult: 验证结果对象
        """
        if not ip or not isinstance(ip, str):
            return ValidationResult(
                is_valid=False,
                error_message="IP地址不能为空且必须为字符串类型"
            )

        ip = ip.strip()

        if len(ip) > self.max_length:
            return ValidationResult(
                is_valid=False,
                error_message=f"IP地址长度超过限制（最大{self.max_length}字符）"
            )

        threats = self._detect_all_threats(ip)
        sanitized = self._sanitize(ip) if self.enable_sanitization else ip

        is_valid_ipv4 = bool(self.IPV4_PATTERN.match(ip))
        is_valid_ipv6 = bool(self.IPV6_PATTERN.match(ip)) if allow_ipv6 else False

        if not is_valid_ipv4 and not is_valid_ipv6:
            return ValidationResult(
                is_valid=False,
                sanitized_value=sanitized,
                error_message="无效的IP地址格式",
                detected_threats=threats
            )

        if threats and self.strict_mode:
            return ValidationResult(
                is_valid=False,
                sanitized_value=sanitized,
                error_message=f"检测到潜在威胁：{', '.join(threats)}",
                detected_threats=threats
            )

        ip_version = "IPv6" if is_valid_ipv6 else "IPv4"
        warnings = []
        if threats and not self.strict_mode:
            warnings.append(f"检测到潜在威胁但已通过验证：{', '.join(threats)}")

        return ValidationResult(
            is_valid=True,
            sanitized_value=sanitized,
            warnings=warnings,
            detected_threats=threats
        )

    def validate_domain(self, domain: str) -> ValidationResult:
        """
        验证域名格式

        Args:
            domain: 待验证的域名字符串

        Returns:
            ValidationResult: 验证结果对象
        """
        if not domain or not isinstance(domain, str):
            return ValidationResult(
                is_valid=False,
                error_message="域名不能为空且必须为字符串类型"
            )

        domain = domain.strip().lower()

        if domain.startswith(('http://', 'https://')):
            return ValidationResult(
                is_valid=False,
                error_message="域名不应包含协议前缀（http/https）"
            )

        if len(domain) > self.max_length:
            return ValidationResult(
                is_valid=False,
                error_message=f"域名长度超过限制（最大{self.max_length}字符）"
            )

        threats = self._detect_all_threats(domain)
        sanitized = self._sanitize(domain) if self.enable_sanitization else domain

        if not self.DOMAIN_PATTERN.match(domain):
            return ValidationResult(
                is_valid=False,
                sanitized_value=sanitized,
                error_message="无效的域名格式",
                detected_threats=threats
            )

        if len(domain) > 253:
            return ValidationResult(
                is_valid=False,
                sanitized_value=sanitized,
                error_message="域名总长度不能超过253个字符",
                detected_threats=threats
            )

        labels = domain.split('.')
        for label in labels:
            if len(label) > 63:
                return ValidationResult(
                    is_valid=False,
                    sanitized_value=sanitized,
                    error_message="域名标签长度不能超过63个字符",
                    detected_threats=threats
                )

        if threats and self.strict_mode:
            return ValidationResult(
                is_valid=False,
                sanitized_value=sanitized,
                error_message=f"检测到潜在威胁：{', '.join(threats)}",
                detected_threats=threats
            )

        warnings = []
        if threats and not self.strict_mode:
            warnings.append(f"检测到潜在威胁但已通过验证：{', '.join(threats)}")

        return ValidationResult(
            is_valid=True,
            sanitized_value=sanitized,
            warnings=warnings,
            detected_threats=threats
        )

    def validate_target(self, target: str) -> ValidationResult:
        """
        自动识别并验证目标（URL/IP/域名）

        Args:
            target: 待验证的目标字符串

        Returns:
            ValidationResult: 验证结果对象
        """
        if not target or not isinstance(target, str):
            return ValidationResult(
                is_valid=False,
                error_message="目标不能为空且必须为字符串类型"
            )

        target = target.strip()

        if target.startswith(('http://', 'https://')):
            return self.validate_url(target)

        if self.IPV4_PATTERN.match(target) or self.IPV6_PATTERN.match(target):
            return self.validate_ip(target)

        if self.DOMAIN_PATTERN.match(target):
            return self.validate_domain(target)

        return ValidationResult(
            is_valid=False,
            error_message="无法识别目标格式，请输入有效的URL、IP地址或域名"
        )

    def detect_sql_injection(self, input_str: str) -> Tuple[bool, List[str]]:
        """
        检测SQL注入特征

        Args:
            input_str: 待检测的输入字符串

        Returns:
            Tuple[bool, List[str]]: (是否检测到威胁, 检测到的特征列表)
        """
        if not input_str:
            return False, []

        detected = []
        for pattern in self.SQL_INJECTION_PATTERNS:
            matches = pattern.findall(input_str)
            if matches:
                detected.extend([str(m) for m in matches if m])

        return len(detected) > 0, list(set(detected))

    def detect_xss(self, input_str: str) -> Tuple[bool, List[str]]:
        """
        检测XSS特征

        Args:
            input_str: 待检测的输入字符串

        Returns:
            Tuple[bool, List[str]]: (是否检测到威胁, 检测到的特征列表)
        """
        if not input_str:
            return False, []

        detected = []
        for pattern in self.XSS_PATTERNS:
            matches = pattern.findall(input_str)
            if matches:
                detected.extend([str(m) for m in matches if m])

        return len(detected) > 0, list(set(detected))

    def detect_command_injection(self, input_str: str) -> Tuple[bool, List[str]]:
        """
        检测命令注入特征

        Args:
            input_str: 待检测的输入字符串

        Returns:
            Tuple[bool, List[str]]: (是否检测到威胁, 检测到的特征列表)
        """
        if not input_str:
            return False, []

        detected = []
        for pattern in self.COMMAND_INJECTION_PATTERNS:
            matches = pattern.findall(input_str)
            if matches:
                detected.extend([str(m) for m in matches if m])

        return len(detected) > 0, list(set(detected))

    def detect_path_traversal(self, input_str: str) -> Tuple[bool, List[str]]:
        """
        检测路径遍历特征

        Args:
            input_str: 待检测的输入字符串

        Returns:
            Tuple[bool, List[str]]: (是否检测到威胁, 检测到的特征列表)
        """
        if not input_str:
            return False, []

        detected = []
        for pattern in self.PATH_TRAVERSAL_PATTERNS:
            matches = pattern.findall(input_str)
            if matches:
                detected.extend([str(m) for m in matches if m])

        return len(detected) > 0, list(set(detected))

    def detect_all_threats(self, input_str: str) -> Dict[str, List[str]]:
        """
        检测所有类型的威胁

        Args:
            input_str: 待检测的输入字符串

        Returns:
            Dict[str, List[str]]: 各类型威胁检测结果
        """
        results = {}

        has_sql, sql_patterns = self.detect_sql_injection(input_str)
        if has_sql:
            results['sql_injection'] = sql_patterns

        has_xss, xss_patterns = self.detect_xss(input_str)
        if has_xss:
            results['xss'] = xss_patterns

        has_cmd, cmd_patterns = self.detect_command_injection(input_str)
        if has_cmd:
            results['command_injection'] = cmd_patterns

        has_path, path_patterns = self.detect_path_traversal(input_str)
        if has_path:
            results['path_traversal'] = path_patterns

        return results

    def sanitize(self, input_str: str, escape_html: bool = True) -> str:
        """
        清洗输入字符串

        Args:
            input_str: 待清洗的输入字符串
            escape_html: 是否转义HTML字符

        Returns:
            str: 清洗后的字符串
        """
        if not input_str:
            return ""

        sanitized = input_str

        if escape_html:
            sanitized = html.escape(sanitized, quote=True)

        return sanitized

    def sanitize_for_sql(self, input_str: str) -> str:
        """
        为SQL查询清洗输入

        Args:
            input_str: 待清洗的输入字符串

        Returns:
            str: 清洗后的字符串
        """
        if not input_str:
            return ""

        sanitized = input_str

        sanitized = sanitized.replace("'", "''")
        sanitized = sanitized.replace("\\", "\\\\")

        dangerous_patterns = [
            ('--', ''),
            ('/*', ''),
            ('*/', ''),
            (';', ''),
        ]

        for pattern, replacement in dangerous_patterns:
            sanitized = sanitized.replace(pattern, replacement)

        return sanitized

    def sanitize_for_shell(self, input_str: str) -> str:
        """
        为Shell命令清洗输入

        Args:
            input_str: 待清洗的输入字符串

        Returns:
            str: 清洗后的字符串
        """
        if not input_str:
            return ""

        sanitized = input_str

        dangerous_chars = ['$', '`', '|', ';', '&', '<', '>', '(', ')', '{', '}', '[', ']', '*', '?', '!', '\n', '\r']

        for char in dangerous_chars:
            sanitized = sanitized.replace(char, '')

        return sanitized

    def _sanitize(self, input_str: str) -> str:
        """
        内部清洗方法

        Args:
            input_str: 待清洗的输入字符串

        Returns:
            str: 清洗后的字符串
        """
        return self.sanitize(input_str)

    def _detect_all_threats(self, input_str: str) -> List[str]:
        """
        内部威胁检测方法

        Args:
            input_str: 待检测的输入字符串

        Returns:
            List[str]: 检测到的威胁类型列表
        """
        threats = self.detect_all_threats(input_str)
        threat_types = []
        for threat_type, patterns in threats.items():
            threat_types.append(threat_type)
            logger.warning(f"检测到{threat_type}威胁: {patterns}")
        return threat_types

    def validate_input(
        self,
        input_str: str,
        input_type: Optional[str] = None,
        custom_patterns: Optional[List[re.Pattern]] = None
    ) -> ValidationResult:
        """
        通用输入验证方法

        Args:
            input_str: 待验证的输入字符串
            input_type: 输入类型（url, ip, domain），为空则自动检测
            custom_patterns: 自定义验证正则表达式列表

        Returns:
            ValidationResult: 验证结果对象
        """
        if not input_str or not isinstance(input_str, str):
            return ValidationResult(
                is_valid=False,
                error_message="输入不能为空且必须为字符串类型"
            )

        input_str = input_str.strip()

        if len(input_str) > self.max_length:
            return ValidationResult(
                is_valid=False,
                error_message=f"输入长度超过限制（最大{self.max_length}字符）"
            )

        threats = self._detect_all_threats(input_str)
        sanitized = self._sanitize(input_str) if self.enable_sanitization else input_str

        if custom_patterns:
            for pattern in custom_patterns:
                if not pattern.match(input_str):
                    return ValidationResult(
                        is_valid=False,
                        sanitized_value=sanitized,
                        error_message="输入不符合自定义验证规则",
                        detected_threats=threats
                    )

        if input_type:
            input_type = input_type.lower()
            if input_type == 'url':
                return self.validate_url(input_str)
            elif input_type == 'ip':
                return self.validate_ip(input_str)
            elif input_type == 'domain':
                return self.validate_domain(input_str)

        if threats and self.strict_mode:
            return ValidationResult(
                is_valid=False,
                sanitized_value=sanitized,
                error_message=f"检测到潜在威胁：{', '.join(threats)}",
                detected_threats=threats
            )

        warnings = []
        if threats and not self.strict_mode:
            warnings.append(f"检测到潜在威胁但已通过验证：{', '.join(threats)}")

        return ValidationResult(
            is_valid=True,
            sanitized_value=sanitized,
            warnings=warnings,
            detected_threats=threats
        )


def create_validator(
    strict_mode: bool = True,
    enable_sanitization: bool = True,
    max_length: int = 2048
) -> InputValidator:
    """
    创建输入验证器实例的工厂函数

    Args:
        strict_mode: 是否启用严格模式
        enable_sanitization: 是否启用输入清洗
        max_length: 最大输入长度限制

    Returns:
        InputValidator: 验证器实例
    """
    return InputValidator(
        strict_mode=strict_mode,
        enable_sanitization=enable_sanitization,
        max_length=max_length
    )


default_validator = InputValidator()
