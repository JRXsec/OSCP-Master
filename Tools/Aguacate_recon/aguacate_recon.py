#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AGUACATE-RECON v1.8
Herramienta de reconocimiento pasivo y activo para auditorías autorizadas.

Uso interactivo:
    python3 aguacate.py
    python3 aguacate.py example.com
"""

import argparse
import ipaddress
import json
import os
import signal
import socket
import ssl
import subprocess
import sys
import time
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

NAME = "AGUACATE-RECON"
VERSION = "1.8"
# Cadenas User-Agent habituales. Son identificadores declarados por el cliente;
# no acreditan el navegador, sistema operativo ni dispositivo real.
USER_AGENTS = {
    "1": ("Chrome en Windows", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"),
    "2": ("Firefox en Windows", "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:143.0) Gecko/20100101 Firefox/143.0"),
    "3": ("Microsoft Edge en Windows", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36 Edg/140.0.0.0"),
    "4": ("Chrome en Linux", "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"),
    "5": ("Firefox en Linux", "Mozilla/5.0 (X11; Linux x86_64; rv:143.0) Gecko/20100101 Firefox/143.0"),
    "6": ("Safari en macOS", "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Safari/605.1.15"),
    "7": ("Chrome en Android", "Mozilla/5.0 (Linux; Android 15; Pixel 9) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Mobile Safari/537.36"),
    "8": ("Safari en iPhone", "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1"),
}
USER_AGENT = USER_AGENTS["1"][1]

COMMON_SUBDOMAINS = [
    "www", "mail", "ftp", "admin", "dev", "test", "staging",
    "api", "vpn", "portal", "blog", "shop", "webmail", "remote",
    "ns1", "ns2", "git", "status",
]


def banner():
    print(r"""
     _    ____ _   _    _    ____    _  _____ _____
    / \  / ___| | | |  / \  / ___|  / \|_   _| ____|
   / _ \| |  _| | | | / _ \| |     / _ \ | | |  _|
  / ___ \ |_| | |_| |/ ___ \ |___ / ___ \| | | |___
 /_/   \_\____|\___//_/   \_\____/_/   \_\_| |_____|

              AGUACATE-RECON v1.7
          Reconocimiento de redes y dominios
    """)


def log(message, verbose=False):
    if verbose:
        print(f"[+] {message}")


def section(title):
    print(f"\n{'=' * 65}\n {title}\n{'=' * 65}")


def highlight_header(name, present=True):
    """Resalta cabeceras relevantes con color y subrayado en terminales compatibles."""
    if not sys.stdout.isatty():
        return name
    # Verde = cabecera recibida; amarillo = cabecera de seguridad ausente.
    color = "\033[1;4;32m" if present else "\033[1;4;33m"
    return f"{color}{name}\033[0m"


def normalize_target(target):
    """Normaliza URL, dominio o dirección IP a un hostname/IP."""
    target = target.strip()
    if "://" in target:
        target = urlparse(target).hostname or ""
    else:
        target = target.split("/", 1)[0].strip()
        # Si parece hostname:puerto, quitar puerto; no alterar IPv6.
        if target.count(":") == 1:
            host, possible_port = target.rsplit(":", 1)
            if possible_port.isdigit():
                target = host

    target = target.strip().rstrip(".")
    if target.startswith("[") and target.endswith("]"):
        target = target[1:-1]
    if not target:
        raise ValueError("El objetivo está vacío o no es válido.")

    try:
        return str(ipaddress.ip_address(target))
    except ValueError:
        pass

    if ":" in target:
        raise ValueError("IPv6 no válida o con formato incorrecto.")
    if len(target) > 253:
        raise ValueError("El nombre del objetivo es demasiado largo.")

    labels = target.rstrip(".").split(".")
    for label in labels:
        if (not label or len(label) > 63 or label.startswith("-")
                or label.endswith("-")
                or not all(c.isalnum() or c == "-" for c in label)):
            raise ValueError(f"Nombre de dominio no válido: {target}")
    return target.lower()


def run_command(command, timeout=30):
    """Ejecuta una herramienta externa y limpia el proceso si se interrumpe."""
    process = None
    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            start_new_session=True,
        )
        try:
            stdout, stderr = process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                stdout, stderr = process.communicate(timeout=3)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                stdout, stderr = process.communicate()
            print(f"[-] Tiempo de espera agotado: {command[0]}")
            return stdout.strip()

        if process.returncode != 0 and stderr.strip():
            print(f"[-] {' '.join(command)}: {stderr.strip()}")
        return stdout.strip()

    except FileNotFoundError:
        print(f"[-] No se encuentra la herramienta: {command[0]}")
    except KeyboardInterrupt:
        if process is not None and process.poll() is None:
            try:
                os.killpg(process.pid, signal.SIGTERM)
                process.wait(timeout=2)
            except (ProcessLookupError, subprocess.TimeoutExpired):
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
        raise
    return ""


def http_get(url, timeout=10):
    """Realiza una petición HTTP GET y devuelve estado, cabeceras y cuerpo."""
    request = Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urlopen(request, timeout=timeout) as response:
            body = response.read(1_000_000).decode("utf-8", errors="replace")
            return {
                "status": response.status,
                "headers": dict(response.headers.items()),
                "body": body,
            }
    except KeyboardInterrupt:
        raise
    except Exception as exc:
        log(f"Petición fallida a {url}: {exc}", True)
        return None


def http_get_json(url, timeout=10):
    result = http_get(url, timeout)
    if not result:
        return None
    try:
        return json.loads(result["body"])
    except (json.JSONDecodeError, TypeError):
        return None


def resolve_addresses(target):
    addresses = set()
    try:
        for result in socket.getaddrinfo(target, None, proto=socket.IPPROTO_TCP):
            addresses.add(result[4][0])
    except socket.gaierror as exc:
        log(f"No se pudo resolver {target}: {exc}", True)
    return sorted(addresses)


# --------------------------- PASIVO ---------------------------

def passive_dns(target, verbose=False):
    section("REGISTROS DNS")
    for record_type in ("A", "AAAA", "MX", "NS", "TXT", "CNAME", "SOA"):
        print(f"\n[*] Registro {record_type}")
        output = run_command([
            "dig", "+time=3", "+tries=1", "+noall", "+answer",
            target, record_type,
        ])
        if output:
            print(output)
        elif verbose:
            print("    Sin resultados o consulta no disponible.")


def dns_subdomains(target, verbose=False):
    section("SUBDOMINIOS COMUNES")
    found = []
    try:
        ipaddress.ip_address(target)
        print("[*] El objetivo es una IP; se omite la búsqueda de subdominios.")
        return found
    except ValueError:
        pass

    for prefix in COMMON_SUBDOMAINS:
        hostname = f"{prefix}.{target}"
        addresses = resolve_addresses(hostname)
        if addresses:
            found.append((hostname, addresses))
            print(f"[+] {hostname}: {', '.join(addresses)}")
        elif verbose:
            print(f"[-] {hostname}: sin resolución")
    if not found:
        print("[*] No se encontraron subdominios en la lista comprobada.")
    print(f"\n[*] Total encontrados: {len(found)}")
    return found


def ip_geolocation(addresses, timeout=10):
    section("INFORMACIÓN DE IP Y RED")
    for address in addresses:
        try:
            ip_obj = ipaddress.ip_address(address)
            if not ip_obj.is_global:
                print(f"[*] {address}: dirección no pública.")
                continue
            data = http_get_json(f"https://ipwho.is/{address}", timeout)
            if not data or not data.get("success", False):
                print(f"[-] No hay datos disponibles para {address}.")
                continue
            connection = data.get("connection") or {}
            print(f"\nIP:           {address}")
            print(f"País:         {data.get('country', 'N/D')}")
            print(f"Región:       {data.get('region', 'N/D')}")
            print(f"Ciudad:       {data.get('city', 'N/D')}")
            print(f"Coordenadas:  {data.get('latitude', 'N/D')}, {data.get('longitude', 'N/D')}")
            print(f"ISP:          {connection.get('isp', 'N/D')}")
            print(f"Organización: {connection.get('org', 'N/D')}")
            print(f"ASN:          {connection.get('asn', 'N/D')}")
        except (ValueError, TypeError) as exc:
            print(f"[-] Error con la IP {address}: {exc}")


def certificate_transparency(target, timeout=15):
    section("CERTIFICATE TRANSPARENCY")
    try:
        ipaddress.ip_address(target)
        print("[*] El objetivo es una IP; se omite la búsqueda por dominio.")
        return
    except ValueError:
        pass

    params = urlencode({"q": f"%.{target}", "output": "json"})
    data = http_get_json(f"https://crt.sh/?{params}", timeout)
    if not isinstance(data, list):
        print("[-] No se pudieron consultar los certificados públicos.")
        return
    names = set()
    for certificate in data:
        for name in certificate.get("name_value", "").splitlines():
            name = name.strip().lower()
            if name and "*" not in name:
                names.add(name)
    if not names:
        print("[*] No se encontraron nombres.")
        return
    for name in sorted(names):
        print(f"[+] {name}")
    print(f"\n[*] Total de nombres únicos: {len(names)}")


def web_history(target, timeout=15):
    section("HISTORIAL WEB")
    try:
        ipaddress.ip_address(target)
        print("[*] El objetivo es una IP; se omite la consulta por dominio.")
        return
    except ValueError:
        pass

    params = urlencode({
        "url": f"*.{target}/*", "output": "json",
        "filter": "statuscode:200", "collapse": "urlkey",
    })
    data = http_get_json(f"https://web.archive.org/cdx/search/cdx?{params}", timeout)
    if not isinstance(data, list) or len(data) < 2:
        print("[*] No se encontraron capturas o el servicio no respondió.")
        return
    print(f"{'FECHA':<18} URL")
    print("-" * 75)
    for entry in data[1:31]:
        if len(entry) >= 3:
            print(f"{entry[1]:<18} {entry[2]}")


def passive_recon(target, verbose=False, timeout=10):
    section(f"{NAME} | MODO PASIVO")
    addresses = resolve_addresses(target)
    if addresses:
        print(f"[*] Objetivo: {target}")
        print(f"[*] IP encontradas: {', '.join(addresses)}")
        ip_geolocation(addresses, timeout)
    else:
        print(f"[-] No se encontraron IP para {target}.")
    passive_dns(target, verbose)
    dns_subdomains(target, verbose)
    certificate_transparency(target, timeout)
    web_history(target, timeout)


# --------------------------- ACTIVO ---------------------------

def tls_inspect(target, port=443, timeout=5):
    section(f"INSPECCIÓN TLS | {target}:{port}")
    context = ssl.create_default_context()
    try:
        with socket.create_connection((target, port), timeout=timeout) as raw:
            with context.wrap_socket(raw, server_hostname=target) as tls:
                cert = tls.getpeercert()
                cipher = tls.cipher()
                print(f"[+] Versión TLS: {tls.version()}")
                print(f"[+] Cifrado: {cipher[0] if cipher else 'N/D'}")
                print(f"[+] Sujeto: {cert.get('subject', 'N/D')}")
                print(f"[+] Emisor: {cert.get('issuer', 'N/D')}")
                print(f"[+] Válido desde: {cert.get('notBefore', 'N/D')}")
                print(f"[+] Válido hasta: {cert.get('notAfter', 'N/D')}")
                sans = cert.get("subjectAltName", ())
                if sans:
                    print("[+] Nombres alternativos:")
                    for kind, name in sans:
                        print(f"    {kind}: {name}")
                print("[+] Certificado validado correctamente.")
    except KeyboardInterrupt:
        raise
    except ssl.SSLCertVerificationError as exc:
        print(f"[-] Falló la validación del certificado: {exc}")
    except (OSError, ssl.SSLError) as exc:
        print(f"[-] Error TLS: {exc}")


def http_headers(target, timeout=10):
    section("CABECERAS HTTP")
    for scheme in ("https", "http"):
        url = f"{scheme}://{target}"
        try:
            request = Request(url, method="HEAD", headers={"User-Agent": USER_AGENT})
            with urlopen(request, timeout=timeout) as response:
                print(f"\n[*] URL: {url}")
                print(f"[*] Estado: {response.status}")
                for name, value in response.headers.items():
                    print(f"{name}: {value}")
        except KeyboardInterrupt:
            raise
        except Exception as exc:
            print(f"[-] {url}: {exc}")


# -------------------- CABECERAS DE SEGURIDAD --------------------

SECURITY_HEADERS = {
    "content-security-policy": (
        "Content-Security-Policy",
        "Reduce el riesgo de XSS y de carga de recursos no autorizados."
    ),
    "strict-transport-security": (
        "Strict-Transport-Security (HSTS)",
        "Indica al navegador que use HTTPS durante un periodo definido."
    ),
    "x-content-type-options": (
        "X-Content-Type-Options",
        "Normalmente debe ser nosniff para evitar MIME sniffing."
    ),
    "x-frame-options": (
        "X-Frame-Options",
        "Puede ayudar a impedir que la página se incruste en un frame."
    ),
    "referrer-policy": (
        "Referrer-Policy",
        "Controla cuánta información de referencia envía el navegador."
    ),
    "permissions-policy": (
        "Permissions-Policy",
        "Permite restringir funciones del navegador disponibles para la página."
    ),
    "cross-origin-opener-policy": (
        "Cross-Origin-Opener-Policy",
        "Ayuda a aislar el contexto de navegación frente a otras ventanas."
    ),
    "cross-origin-resource-policy": (
        "Cross-Origin-Resource-Policy",
        "Controla qué otros orígenes pueden cargar este recurso."
    ),
    "cross-origin-embedder-policy": (
        "Cross-Origin-Embedder-Policy",
        "Controla la carga de recursos cross-origin para aislamiento."
    ),
}

DEFAULT_WEB_PATHS = [
    "/", "/login", "/admin", "/api", "/robots.txt",
    "/.well-known/security.txt",
]


def normalize_web_base(raw_target):
    """Acepta una URL HTTP(S) completa o un dominio y devuelve su URL base."""
    raw_target = raw_target.strip()
    if not raw_target:
        raise ValueError("La URL está vacía.")
    if "://" not in raw_target:
        raw_target = "https://" + raw_target
    parsed = urlparse(raw_target)
    if parsed.scheme.lower() not in ("http", "https"):
        raise ValueError("Solo se admiten URLs http:// o https://.")
    if not parsed.hostname:
        raise ValueError("La URL no contiene un dominio válido.")
    # Validar el host con la misma función usada por el resto de la herramienta.
    normalize_target(parsed.hostname)
    if parsed.username or parsed.password:
        raise ValueError("No incluyas credenciales en la URL.")
    return f"{parsed.scheme.lower()}://{parsed.netloc}", parsed.path or "/"


def fetch_headers_for_url(url, timeout=10):
    """Hace una petición GET ligera y devuelve estado, URL final y cabeceras."""
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "*/*"}, method="GET")
    try:
        with urlopen(request, timeout=timeout) as response:
            # No hace falta descargar el cuerpo para analizar las cabeceras.
            response.read(1)
            return {
                "status": response.status,
                "url": response.geturl(),
                "headers": response.headers,
            }
    except KeyboardInterrupt:
        raise
    except Exception as exc:
        return {"error": str(exc)}


def security_headers_recon(raw_target, timeout=10, verbose=False):
    """Analiza cabeceras de seguridad en la URL raíz y en varias rutas."""
    try:
        base_url, original_path = normalize_web_base(raw_target)
    except ValueError as exc:
        print(f"[-] URL no válida: {exc}")
        return

    section("ANÁLISIS DE CABECERAS DE SEGURIDAD")
    print("[*] Se realizarán peticiones GET a las rutas seleccionadas.")
    print("[*] Analiza únicamente webs propias o para las que tengas autorización.")
    user_agent_line = f"User-Agent enviado: {USER_AGENT}"
    if sys.stdout.isatty():
        user_agent_line = f"\033[1;34m{user_agent_line}\033[0m"
    print(f"\n[+] Cabecera de petición enviada: {user_agent_line}")
    entered = input(
        "Rutas separadas por comas (Enter para rutas comunes): "
    ).strip()
    if entered:
        paths = []
        for item in entered.split(","):
            path = item.strip()
            if not path:
                continue
            if not path.startswith("/"):
                path = "/" + path
            if path not in paths:
                paths.append(path)
    else:
        paths = list(DEFAULT_WEB_PATHS)
        if original_path and original_path != "/":
            paths.insert(0, original_path)

    if not paths:
        print("[-] No se han indicado rutas.")
        return

    parsed_base = urlparse(base_url)
    alternate_base = ("http://" if parsed_base.scheme == "https" else "https://") + parsed_base.netloc
    any_success = False

    for path in paths:
        # Evitar que una ruta introducida pueda convertirse en una URL de otro host.
        path = "/" + path.lstrip("/")
        url = base_url.rstrip("/") + path
        result = fetch_headers_for_url(url, timeout)
        if result.get("error") and parsed_base.scheme == "https":
            if verbose:
                print(f"[VERBOSE] HTTPS falló para {path}; probando HTTP como alternativa.")
            fallback = fetch_headers_for_url(alternate_base.rstrip("/") + path, timeout)
            if not fallback.get("error"):
                result = fallback
        if result.get("error"):
            print(f"\n[-] {url}: {result['error']}")
            continue

        any_success = True
        headers = result["headers"]
        lower_headers = {name.lower(): value for name, value in headers.items()}
        print(f"\n{'-' * 68}")
        print(f"[*] Ruta: {path}")
        print(f"[*] URL final: {result['url']}")
        print(f"[*] Estado HTTP: {result['status']}")
        print("\n[+] Cabeceras de seguridad:")
        if sys.stdout.isatty():
            print("    Leyenda: \033[1;4;32mverde subrayado = presente\033[0m; "
                  "\033[1;4;33mamarillo subrayado = ausente\033[0m")
        for key, (display_name, explanation) in SECURITY_HEADERS.items():
            value = lower_headers.get(key)
            if value:
                highlighted = highlight_header(display_name, present=True)
                print(f"  [OK] {highlighted}: {value}")
            else:
                highlighted = highlight_header(display_name, present=False)
                print(f"  [--] {highlighted}: ausente")
                if verbose:
                    print(f"       {explanation}")

        cookies = headers.get_all("Set-Cookie") or []
        if cookies:
            print("\n[+] Cookies recibidas:")
            for cookie in cookies:
                # Mostrar atributos sin volcar el valor de la cookie.
                parts = [part.strip() for part in cookie.split(";")]
                cookie_name = parts[0].split("=", 1)[0] if parts else "(sin nombre)"
                attributes = {part.lower() for part in parts[1:]}
                secure = any(part == "secure" for part in attributes)
                httponly = any(part == "httponly" for part in attributes)
                samesite = next((part for part in parts[1:] if part.lower().startswith("samesite=")), None)
                print(f"  - {cookie_name}: Secure={'sí' if secure else 'no'}, HttpOnly={'sí' if httponly else 'no'}, {samesite or 'SameSite no indicado'}")
        elif verbose:
            print("\n[VERBOSE] La respuesta no incluye Set-Cookie.")

        print("\n[+] Otras cabeceras de respuesta:")
        for name, value in headers.items():
            if name.lower() not in SECURITY_HEADERS and name.lower() != "set-cookie":
                print(f"  {name}: {value}")

    if not any_success:
        print("\n[-] No se pudo obtener una respuesta HTTP de las rutas indicadas.")
    print("\n[*] Nota: una cabecera ausente es una señal para revisar, no una vulnerabilidad confirmada por sí sola.")


def nmap_scan(target, top_ports=100, version=False, timeout=120):
    section("ESCANEO NMAP")
    command = ["nmap", "-Pn", "--top-ports", str(top_ports)]
    if version:
        command.append("-sV")
    command.append(target)
    print("[*] Ejecutando:", " ".join(command))
    output = run_command(command, timeout=timeout)
    if output:
        print(output)
    else:
        print("[-] Sin resultados. Comprueba que Nmap esté instalado.")


def active_recon(target, tls_port=443, do_http=True, do_ports=True,
                 top_ports=100, version=False, timeout=10):
    section(f"{NAME} | MODO ACTIVO")
    tls_inspect(target, tls_port, timeout)
    if do_http:
        http_headers(target, timeout)
    if do_ports:
        nmap_scan(target, top_ports=top_ports, version=version,
                   timeout=max(timeout, 120))


# --------------------------- CLI ---------------------------

def build_parser():
    parser = argparse.ArgumentParser(
        prog="aguacate.py",
        description="AGUACATE-RECON: reconocimiento para auditorías autorizadas.",
    )
    parser.add_argument("target", nargs="?", help="Dominio, hostname o dirección IP (opcional; también se puede introducir en el menú).")
    parser.add_argument("--tls-port", type=int, default=443, help="Puerto TLS (por defecto: 443).")
    parser.add_argument("--top-ports", type=int, default=100, help="Número de puertos TCP para Nmap.")
    parser.add_argument("--no-http", action="store_true", help="Omitir cabeceras HTTP en el modo activo.")
    parser.add_argument("--no-ports", action="store_true", help="Omitir el escaneo Nmap en el modo activo.")
    parser.add_argument("--version", action="store_true", help="Identificar servicios y versiones con Nmap.")
    parser.add_argument("--timeout", type=int, default=10, help="Tiempo de espera de red en segundos.")
    parser.add_argument("-v", "--verbose", action="store_true", help="Mostrar mensajes adicionales sin preguntar.")
    # Compatibilidad con los modos antiguos; ya no hacen falta para usar el menú.
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--passive", action="store_true", help=argparse.SUPPRESS)
    modes.add_argument("--active", action="store_true", help=argparse.SUPPRESS)
    modes.add_argument("--all", action="store_true", help=argparse.SUPPRESS)
    return parser


def choose_mode():
    """Muestra un menú numerado y devuelve el modo seleccionado."""
    while True:
        print("\n¿Qué tipo de reconocimiento quieres ejecutar?\n")
        print("  1) PASIVO  — consultas a fuentes públicas y DNS; no escanea puertos del objetivo.")
        print("     Incluye IP/DNS, información aproximada de red, subdominios comunes, crt.sh y Wayback.")
        print("  2) ACTIVO  — conecta directamente con el objetivo para comprobar TLS, cabeceras HTTP y puertos con Nmap.")
        print("     Úsalo únicamente en sistemas propios o con autorización explícita.")
        print("  3) COMPLETO — ejecuta primero el reconocimiento pasivo y después el activo.")
        print("  4) CABECERAS WEB — analiza cabeceras de seguridad en varias rutas HTTP/HTTPS.")
        print("     No crea un servidor local; envía peticiones a la web que indiques.")
        print("  5) SALIR")
        choice = input("\nSelecciona una opción [1-5]: ").strip()
        if choice == "1":
            return "passive"
        if choice == "2":
            return "active"
        if choice == "3":
            return "all"
        if choice == "4":
            return "headers"
        if choice == "5":
            return None
        print("[!] Opción no válida. Escribe 1, 2, 3, 4 o 5.")


def choose_user_agent():
    """Permite elegir el User-Agent que usarán las peticiones de la opción 4."""
    global USER_AGENT
    print("\nSelecciona el User-Agent para el análisis de cabeceras:")
    for key, (label, _value) in USER_AGENTS.items():
        print(f"  {key}) {label}")
    print("  9) Usar uno personalizado")
    while True:
        choice = input("Opción [1-9, por defecto 1]: ").strip() or "1"
        if choice in USER_AGENTS:
            label, USER_AGENT = USER_AGENTS[choice]
            break
        if choice == "9":
            custom = input("Introduce el User-Agent personalizado: ").strip()
            if custom and "\r" not in custom and "\n" not in custom:
                label, USER_AGENT = "Personalizado", custom
                break
            print("[!] El User-Agent no puede estar vacío ni contener saltos de línea.")
            continue
        print("[!] Opción no válida. Elige un número del 1 al 9.")
    line = f"{label}: {USER_AGENT}"
    if sys.stdout.isatty():
        line = f"\033[1;34m{line}\033[0m"
    print(f"[+] User-Agent seleccionado: {line}")


def ask_verbose(default=False):
    if default:
        return True
    while True:
        answer = input("¿Mostrar mensajes adicionales (verbose)? [s/N]: ").strip().lower()
        if answer in ("s", "si", "sí", "y", "yes"):
            return True
        if answer in ("", "n", "no"):
            return False
        print("[!] Responde s o n.")


def main():
    parser = build_parser()
    args = parser.parse_args()
    banner()

    # Si se ha especificado un modo antiguo, se respeta. Si no, se muestra el menú.
    if args.passive:
        mode = "passive"
    elif args.active:
        mode = "active"
    elif args.all:
        mode = "all"
    else:
        mode = choose_mode()
        if mode is None:
            print("[*] Saliendo de AGUACATE-RECON.")
            return

    if mode == "headers":
        choose_user_agent()

    raw_target = args.target
    if not raw_target:
        raw_target = input("Introduce el dominio, hostname o IP objetivo: ").strip()
    if mode == "headers":
        try:
            target, _ = normalize_web_base(raw_target)
        except ValueError as exc:
            parser.error(str(exc))
    else:
        try:
            target = normalize_target(raw_target)
        except ValueError as exc:
            parser.error(str(exc))

    if not 1 <= args.tls_port <= 65535:
        parser.error("--tls-port debe estar entre 1 y 65535.")
    if not 1 <= args.top_ports <= 65535:
        parser.error("--top-ports debe estar entre 1 y 65535.")
    if args.timeout < 1:
        parser.error("--timeout debe ser mayor que cero.")

    verbose = args.verbose or ask_verbose()
    print(f"[*] Objetivo: {target}")
    print(f"[*] Inicio: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"[*] Modo seleccionado: {mode.upper()}")

    if mode in ("passive", "all"):
        passive_recon(target, verbose=verbose, timeout=args.timeout)
    if mode in ("active", "all"):
        active_recon(
            target,
            tls_port=args.tls_port,
            do_http=not args.no_http,
            do_ports=not args.no_ports,
            top_ports=args.top_ports,
            version=args.version,
            timeout=args.timeout,
        )
    if mode == "headers":
        security_headers_recon(raw_target, timeout=args.timeout, verbose=verbose)
    print(f"\n[+] {NAME} finalizado.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n[!] {NAME} detenido por el usuario.", flush=True)
        sys.exit(130)
