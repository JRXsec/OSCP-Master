# AGUACATE-RECON

## Descripción del proyecto

Crear un script en Python que realice tareas de enumeración pasiva y activa vistas en clase, así como el análisis de cabeceras de seguridad HTTP. La herramienta también permite estudiar cómo responde una web ante distintos valores de la cabecera `User-Agent`.

Se investiga el uso del User-Agent y su influencia en las respuestas de los servidores web.

Se prioriza que la herramienta presente la información recopilada de forma clara y organizada.

## Resumen de la herramienta

Esta herramienta es interactiva, está programada en Python 3 y permite realizar tareas de reconocimiento web y de infraestructura, tanto pasivas como activas, además de analizar cabeceras HTTP, configuraciones de seguridad y respuestas del servidor.

## Modos de uso

1. **Reconocimiento pasivo:** recopila información DNS, direcciones IP, geolocalización aproximada, ISP/ASN, subdominios comunes, certificados públicos mediante `crt.sh` e historial de Wayback Machine.
2. **Reconocimiento activo:** comprueba certificados TLS, cabeceras HTTP y puertos abiertos mediante Nmap, con detección de versiones opcional.
3. **Reconocimiento completo:** combina el reconocimiento pasivo y el activo.
4. **Análisis de cabeceras web:** examina cabeceras de seguridad como CSP, HSTS y X-Frame-Options, además de códigos de estado HTTP, cookies, redirecciones y rutas comunes. Permite seleccionar distintos perfiles de User-Agent para comparar las respuestas del servidor.
5. **Salir:** cierra la herramienta.

## Capturas de las pruebas

### Reconocimiento completo (pasivo + activo)

En las siguientes capturas se muestra el resultado del reconocimiento completo.

![Reconocimiento pasivo: registros DNS y subdominios comunes](Pasted%20image%2020261014203305.png)

En esta captura se puede observar una ejecución sin el modo verbose, lo que permite obtener una salida más limpia con los registros DNS y los subdominios comunes.

![Certificados TLS y cabeceras HTTP](Pasted%20image%2020261014203402.png)

Aquí se muestran los certificados TLS y algunas de las cabeceras HTTP detectadas.

![Cabeceras y escaneo de puertos con Nmap](Pasted%20image%2020261014203521.png)

En esta última parte se muestran más cabeceras y un análisis rápido de los 100 puertos más comunes mediante Nmap.

### Análisis de cabeceras web (opción 4)

![Selector de User-Agent](Pasted%20image%2020261014205839.png)

La herramienta permite seleccionar distintos perfiles de User-Agent para comprobar cómo responde una web ante diferentes agentes.

![
