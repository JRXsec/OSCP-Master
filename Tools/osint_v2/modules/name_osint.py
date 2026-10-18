"""
modules/name_osint.py — Nombre completo: búsquedas dirigidas en buscadores y
redes con TODAS las combinaciones del nombre (Pepe Pepito García ->
"Pepe Pepito García", "Pepe García", "Pepe Pepito", ...). La búsqueda de
cuentas por username la hace modules/username.py.
"""
from urllib.parse import quote, quote_plus

from core.registry import register, result
from core.utils import (accent_forms, has_accents, linkedin_slugs, name_combos,
                        name_variants, search_links)


@register(name="name_search", title="Búsquedas del nombre", accepts=["name"])
def name_search(name: str, ctx) -> dict:
    combos = [" ".join(c) for c in name_combos(name)]
    # Con y sin tildes: "Pepe García" y "Pepe Garcia" dan resultados distintos
    # en LinkedIn/Facebook según cómo lo escribiera la persona.
    # Google admite ~32 palabras por consulta: se usan las 4 primeras combinaciones
    any_name = " OR ".join(f'"{f}"' for c in combos[:4] for f in accent_forms(c))
    links = search_links([
        ("Google: cualquier forma del nombre", any_name),
        ("Google: LinkedIn", f"({any_name}) site:linkedin.com/in"),
        ("Google: Facebook", f"({any_name}) site:facebook.com"),
        ("Google: Instagram", f"({any_name}) site:instagram.com"),
        ("Google: X / Twitter", f"({any_name}) site:x.com OR site:twitter.com"),
        ("Google: TikTok", f"({any_name}) site:tiktok.com"),
        ("Google: documentos (PDF, Excel, Word)",
         f"({any_name}) filetype:pdf OR filetype:xlsx OR filetype:docx"),
        ("Google: boletines oficiales",
         f"({any_name}) site:boe.es OR site:dof.gob.mx OR site:gob.mx"),
    ])
    for c in combos:
        for f in accent_forms(c):
            tag = "con tildes" if has_accents(f) else \
                ("sin tildes" if has_accents(c) else "")
            links.append({"label": f'Google: "{f}"', "url": "https://www.google.com/"
                          "search?q=" + quote_plus(f'"{f}"'),
                          "extra": "nombre exacto" + (f" · {tag}" if tag else "")})
    for slug in linkedin_slugs(name):
        links.append({"label": f"LinkedIn /in/{slug}",
                      "url": f"https://www.linkedin.com/in/{quote(slug)}",
                      "extra": "perfil probable (comprobar a mano)" +
                               (" · con tildes" if has_accents(slug) else "")})
    for f in accent_forms(name.strip()):
        links += [
            {"label": f"LinkedIn (buscador): {f}",
             "url": "https://www.linkedin.com/search/results/people/?keywords=" + quote(f)},
            {"label": f"Facebook (buscador): {f}",
             "url": "https://www.facebook.com/search/people/?q=" + quote(f)},
        ]
    links.append({"label": "Google Imágenes",
                  "url": "https://www.google.com/search?tbm=isch&q=" + quote_plus(any_name)})
    users = name_variants(name, 8)
    if has_accents(name):
        users += [v for v in name_variants(name, 3, accents=True) if v not in users]
    fields = {"Combinaciones del nombre": "\n".join(combos),
              "Usernames que se prueban": ", ".join(users)}
    return result("name_search", "Búsquedas del nombre", "info",
                  f"{len(combos)} combinaciones · {len(links)} búsquedas preparadas",
                  fields, links,
                  ["LinkedIn exige iniciar sesión, así que los perfiles /in/ "
                   "no se pueden comprobar automáticamente: ábrelos a mano."])
