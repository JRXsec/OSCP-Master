# AGUACATE-RECON

## Project description

Build a Python script that performs the passive and active enumeration techniques covered in class, along with an analysis of HTTP security headers. The tool also makes it possible to study how a website responds to different values of the `User-Agent` header.

It also looks into the `User-Agent` header and how it influences web server responses.

The focus is on presenting the collected information in a clear and organized way.

![Assignment statement](assets/Pasted%20image%2020261014183352.png)

## Tool overview

This is an interactive tool written in Python 3. It performs passive and active web and infrastructure reconnaissance, and analyzes HTTP headers, security settings and server responses.

## Usage modes

1. **Passive reconnaissance:** gathers DNS information, IP addresses, approximate geolocation, ISP/ASN, common subdomains, public certificates via `crt.sh` and Wayback Machine history.
2. **Active reconnaissance:** checks TLS certificates, HTTP headers and open ports with Nmap, with optional version detection.
3. **Full reconnaissance:** combines passive and active reconnaissance.
4. **Web header analysis:** examines security headers such as CSP, HSTS and X-Frame-Options, as well as HTTP status codes, cookies, redirects and common paths. Lets you pick different User-Agent profiles to compare the server's responses.
5. **Exit:** closes the tool.

## Test screenshots

### Full reconnaissance (passive + active)

The following screenshots show the output of a full reconnaissance run.

![Passive reconnaissance: DNS records and common subdomains](assets/Pasted%20image%2020261014203305.png)

This run was done without verbose mode, which gives a cleaner output with the DNS records and common subdomains.

![TLS certificates and HTTP headers](assets/Pasted%20image%2020261014203402.png)

Here you can see the TLS certificates and some of the detected HTTP headers.

![Headers and Nmap port scan](assets/Pasted%20image%2020261014203521.png)

This last part shows more headers and a quick scan of the 100 most common ports with Nmap.

### Web header analysis (option 4)

![User-Agent selector](assets/Pasted%20image%2020261014205839.png)

The tool lets you choose from several User-Agent profiles to check how a website responds to different agents.

![Response headers using Chrome on Android 15](assets/Pasted%20image%2020261014210407.png)

Here you can see the response headers when the request is sent as Chrome on Android 15: security headers present and missing, cookies and their flags, and other response headers.

## User-Agent research

The `User-Agent` is a very important header when analyzing a website, because the page can behave differently depending on the agent, applying filters based on the client.

For example, a server may return a different response depending on whether the request comes from Chrome, Firefox or Safari, or even block certain requests if it detects an agent it considers suspicious.

This can help identify basic filters, access restrictions or server-specific configurations.
