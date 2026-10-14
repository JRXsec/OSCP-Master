Crear script en Python que haga la enumeración pasiva y activa que se ha visto en clase, también crear otro script en el que recoja información de las cabeceras de seguridad al hacer una petición a cualquier sitio, con ello , crea un servidor HTTP y captura las cabeceras “user-agent” de las peticiones.  

Investiga que se puede hacer con el user-agent a grandes rasgos

Puntuara positivamente como la herramienta enseña la información recopilada

Script enumeración pasiva y activa.


**Resumen de la herramienta:**

Esta herramienta es interactiva, está programada en python3 y 


**Modos de uso:**

1. Reconocimiento pasivo: recopila información DNS, IP, geolocalización aproximada, ISP/ASN, subdominios comunes, certificados públicos mediante "crt.sh" e historial de "Wayback Machine".

2. Reconocimiento activo: comprueba certificados TLS, cabeceras HTTP y puertos abiertos mediante Nmap, con detección de versiones opcional.

3. Reconocimiento completo: combina el reconocimiento pasivo y el activo.

4. Análisis de cabeceras web: examina cabeceras de seguridad como "CSP", "HSTS" y "X-Frame-Options" según cómo responde a las peticiones HTTP que le enviamos y qué información expone.

5. Salir: cierra la herramienta.


**Capturas de las pruebas con un servidor web.**

Capturas del modo de análisis completo (Pasivo + Activo)

![[Pasted image 20261014203305.png]]
En esta se puede observar que no elegimos el modo Verbose para tener una respuesta más limpia, 
los registros dns y los subdominios comunes.

![[Pasted image 20261014203402.png]]
Aquí se pueden ver los certificados TLS y algunas cabeceras.




![[Pasted image 20261014203521.png]]
Aquí terminamos de ver algunas cabeceras y un análisis rápido de los 100 puertos mas comunes en nmap.


Capturas opción 4 Cabeceras Web:

![[Pasted image 20261014205839.png]]
Aquí podemos ver las opciones de diferentes user-agents que podemos pre-seleccionar para ver como responde la web.

![[Pasted image 20261014210407.png]]
Aquí vemos las cabeceras de respuesta con un navegador mozilla en un Android 15.


**Investigación sobre el user-agent.**

El user-agent es una cabecera muy importante a la hora de hacer un análisis sobre una web ya que la página se puede comportar de forma diferente dependiendo de el agente aplicando filtros sobre el cliente.

Por ejemplo, un servidor puede devolver una respuesta diferente dependiendo de si la petición procede de Chrome, Firefox o Safari, o incluso bloquear determinadas peticiones si detecta un agente que considera sospechoso. 

Esto puede ayudarnos a identificar filtros básicos, restricciones de acceso o configuraciones específicas del servidor.