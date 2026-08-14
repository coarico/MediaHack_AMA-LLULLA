import ipaddress
import socket
from urllib.parse import urlparse


PRIVATE_HOSTNAMES = {"localhost"}


class UnsafeUrlError(ValueError):
    pass


def validate_public_http_url(raw_url: str) -> str:
    parsed = urlparse(raw_url.strip())
    if parsed.scheme not in {"http", "https"}:
        raise UnsafeUrlError("Solo se permiten URLs http o https.")
    if not parsed.netloc:
        raise UnsafeUrlError("La URL no tiene dominio valido.")
    hostname = parsed.hostname
    if not hostname:
        raise UnsafeUrlError("La URL no tiene hostname valido.")
    if hostname.lower() in PRIVATE_HOSTNAMES:
        raise UnsafeUrlError("No se permite acceder a hosts locales.")

    try:
        ip = ipaddress.ip_address(hostname)
        _reject_private_ip(ip)
    except ValueError:
        _validate_resolved_addresses(hostname)

    return raw_url.strip()


def _validate_resolved_addresses(hostname: str) -> None:
    try:
        addresses = socket.getaddrinfo(hostname, None)
    except socket.gaierror as exc:
        raise UnsafeUrlError("No se pudo resolver el dominio.") from exc

    for address in addresses:
        ip = ipaddress.ip_address(address[4][0])
        _reject_private_ip(ip)


def _reject_private_ip(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> None:
    if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_reserved:
        raise UnsafeUrlError("No se permiten IPs privadas, locales o reservadas.")

