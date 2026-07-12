"""Served legal pages: /legal/privacy and /legal/terms.

Condensed, RO-primary, self-contained HTML derived from the DRAFT compliance pack in
``docs/compliance/`` — enough to link from the consent gate and give visitors a real
notice. It is DELIBERATELY marked DRAFT and carries ``[[PLACEHOLDER]]`` controller fields:
the full documents in ``docs/compliance/`` must be completed and reviewed by a Romanian
data-protection lawyer before go-live (see docs/DEPLOY.md go-live checklist).

Always mounted (both modes) so the anonymous arcade also has a reachable privacy/cookie
notice. Reads no database.
"""

from __future__ import annotations

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.utils.html import escape

_SHELL = """<!doctype html>
<html lang="ro"><head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{title} · cât-de-român-ești</title>
<style>
  body {{ margin:0; padding:2rem 1rem; font-family: system-ui, sans-serif; color:#e8e8f0;
    background: radial-gradient(1200px 800px at 30% 20%, #1b2350, #0a0d1f 70%); }}
  main {{ max-width: 46rem; margin: 0 auto; }}
  h1 {{ font-size: 1.7rem; }}
  h2 {{ margin-top: 1.8rem; font-size: 1.15rem; color:#ffd166; }}
  a {{ color:#84d6ff; }}
  .draft {{ background: rgba(255,84,112,0.14); border:1px solid rgba(255,84,112,0.4);
    border-radius:10px; padding:.7rem 1rem; margin:1rem 0; font-size:.92rem; }}
  code {{ background: rgba(255,255,255,0.08); padding:.1rem .35rem; border-radius:5px; }}
  li {{ line-height:1.55; }} p {{ line-height:1.6; }}
  footer {{ margin-top:2rem; font-size:.85rem; color:#9a93c0; }}
</style></head><body><main>
{body}
<footer><a href="/">← Înapoi la joc</a></footer>
</main></body></html>
"""


def _draft_banner(*, show_unfinalized: bool) -> str:
    # The draft / lawyer-review-pending wording always applies; the "not finalized yet"
    # sentence only holds while the operator identity and contact are unset (CAT_LEGAL_OPERATOR
    # / CAT_LEGAL_CONTACT_EMAIL, see web/settings.py).
    unfinalized = (
        " Operatorul și datele de contact nu sunt încă finalizate." if show_unfinalized else ""
    )
    return (
        '<div class="draft"><strong>DRAFT — text în lucru.</strong> Acest document trebuie '
        "completat și verificat de un avocat specializat în protecția datelor înainte de "
        f"publicare.{unfinalized}</div>"
    )


def _contact_html(contact_email: str) -> str:
    if not contact_email:
        return "<code>[[PLACEHOLDER: contact]]</code>"
    safe = escape(contact_email)
    return f'<a href="mailto:{safe}">{safe}</a>'


def _operator_line_html(operator: str) -> str:
    if not operator:
        return ""
    return f"Operatorul serviciului este <strong>{escape(operator)}</strong>. "


_PRIVACY_BODY = """
<h1>Politica de confidențialitate</h1>
{draft}
<p><em>cât-de-român-ești</em> este un joc de cuvinte gratuit, în limba română. Poți juca
<strong>fără cont</strong>; progresul se salvează local în browser. Dacă folosești
„Intră cu Google”, îți putem salva progresul și pe server.</p>

<h2>Ce date colectăm</h2>
<ul>
  <li><strong>Cont Google</strong> (dacă te autentifici): adresa de e-mail, numele și poza
    de profil furnizate de Google, plus identificatorul contului. Nu stocăm parole și nu
    păstrăm tokenurile Google.</li>
  <li><strong>Progres în joc</strong>: istoricul scorurilor, completările zilnice și cele
    mai bune rezultate pe puzzle.</li>
  <li><strong>Date tehnice</strong>: adresa IP și jurnale de securitate strict necesare
    funcționării și protecției serviciului.</li>
</ul>

<h2>De ce și pe ce temei</h2>
<ul>
  <li>Contul și salvarea progresului — pe baza <strong>consimțământului</strong> tău.</li>
  <li>Securitatea serviciului — pe baza interesului legitim.</li>
</ul>

<h2>Copii</h2>
<p>În România, consimțământul pentru un cont este valabil de la <strong>16 ani</strong>.
Sub 16 ani este nevoie de acordul unui părinte sau tutore; până atunci nu creăm cont și nu
salvăm progres pe server — jocul rămâne disponibil fără cont.</p>

<h2>Unde stau datele și cine le prelucrează</h2>
<p>Datele de cont și progres sunt găzduite în <strong>UE/SEE</strong>. Prelucrători:
Google (autentificare), furnizorul de găzduire (UE) și rețeaua de livrare/CDN. Nu folosim
cookie-uri de publicitate sau de urmărire.</p>

<h2>Drepturile tale</h2>
<p>Ai dreptul de acces, rectificare, ștergere, portabilitate, opoziție și de retragere a
consimțământului. Îți poți <strong>șterge contul și tot progresul</strong> direct din meniul
contului. {operator_line}Pentru orice cerere sau plângere: {contact}. Te poți
adresa și autorității de supraveghere, <strong>ANSPDCP</strong>.</p>

<p>Documentul complet (draft): <code>docs/compliance/privacy-notice.md</code>.</p>
"""

_TERMS_BODY = """
<h1>Termeni și condiții</h1>
{draft}
<h2>1. Serviciul</h2>
<p><em>cât-de-român-ești</em> este un joc educațional gratuit. Poți juca fără cont; contul
prin Google este opțional și servește doar la salvarea progresului.</p>

<h2>2. Eligibilitate și vârstă</h2>
<p>Pentru crearea unui cont trebuie să ai cel puțin <strong>16 ani</strong>; sub această
vârstă este necesar acordul unui părinte/tutore.</p>

<h2>3. Utilizare acceptabilă</h2>
<p>Nu utiliza serviciul în mod abuziv, nu încerca să îl perturbi și nu accesa conturi care
nu îți aparțin.</p>

<h2>4. Fără garanții / limitarea răspunderii</h2>
<p>Serviciul este oferit „ca atare”, fără garanții. În limitele permise de lege, răspunderea
este limitată.</p>

<h2>5. Legea aplicabilă</h2>
<p>Se aplică legea din <strong>România</strong>.</p>

<h2>6. Modificări</h2>
<p>Putem actualiza acești termeni; la modificări importante îți vom cere o nouă acceptare.</p>

<p>Document complet (draft): <code>docs/compliance/terms-of-service.md</code>.</p>
"""


def _page(title: str, body: str) -> HttpResponse:
    version = getattr(settings, "CAT_CONSENT_VERSION", "")
    footer_note = f"<p class='draft'>Versiune schiță: <code>{version}</code></p>" if version else ""
    html = _SHELL.format(title=title, body=body + footer_note)
    return HttpResponse(html, content_type="text/html; charset=utf-8")


def privacy(request: HttpRequest) -> HttpResponse:
    operator = (getattr(settings, "CAT_LEGAL_OPERATOR", "") or "").strip()
    contact_email = (getattr(settings, "CAT_LEGAL_CONTACT_EMAIL", "") or "").strip()
    body = _PRIVACY_BODY.format(
        draft=_draft_banner(show_unfinalized=not (operator and contact_email)),
        operator_line=_operator_line_html(operator),
        contact=_contact_html(contact_email),
    )
    return _page("Confidențialitate", body)


def terms(request: HttpRequest) -> HttpResponse:
    operator = (getattr(settings, "CAT_LEGAL_OPERATOR", "") or "").strip()
    contact_email = (getattr(settings, "CAT_LEGAL_CONTACT_EMAIL", "") or "").strip()
    body = _TERMS_BODY.format(
        draft=_draft_banner(show_unfinalized=not (operator and contact_email)),
    )
    return _page("Termeni", body)
