#!/usr/bin/env python3
"""
Page-chrome translations for the Anchorage Summer Meals page.

SCOPE: only the page *chrome* is translated here -- headings, labels, buttons,
notes, and footer. The site listings themselves (names, addresses, comments,
times) are shown exactly as USDA provides them and are NOT translated.

>>> THESE TRANSLATIONS ARE MACHINE-DRAFTED AND NEED HUMAN REVIEW. <<<
Do not treat them as final for a public food-access page. Before launch, route
each locale through the Municipality of Anchorage's language-access resources
(or a qualified community translator). The Spanish is the most reliable; the
Hmong, Samoan, and Tagalog strings especially need a native-speaker pass. Each
non-English page renders a visible "awaiting human review" banner (see
`review_note`) until that review happens -- remove the banner only after sign-off.

This is a first-party data module (standard library only, no imports), so it
does not affect generate.py's "no third-party runtime dependencies" rule.

Adding a language: append to LOCALES and add a matching block to STRINGS with
the same keys as the English ("en") block, then run generate.py.
"""

# Order here is the order shown in the language switcher. English first.
LOCALES = [
    {"code": "en",  "name": "English",        "needs_review": False},
    {"code": "es",  "name": "Español",   "needs_review": True},
    {"code": "hmn", "name": "Hmoob",          "needs_review": True},
    {"code": "sm",  "name": "Gagana Sāmoa", "needs_review": True},
    {"code": "tl",  "name": "Tagalog",        "needs_review": True},
]

# Every block must define the same keys as "en". "days"/"days_abbr" are 7-long
# (Mon..Sun). "meals" / "models" map the English label produced by generate.py
# to the localized label.
STRINGS = {
    "en": {
        "html_lang": "en",
        "review_note": "",
        "title": "Free Summer Meals in Anchorage",
        "meta_desc": "Free summer meals for kids 18 and under in Anchorage, "
                     "Alaska. See sites open today and all week.",
        "skip": "Skip to today’s meals",
        "h1": "Free Summer Meals in Anchorage",
        "sub": "Free breakfast, lunch, and snacks for anyone 18 and under. "
               "No sign-up, no ID, and no cost.",
        "lang_label": "Language",
        "updated": "Updated",
        "open_today_one": "{n} site open today",
        "open_today_many": "{n} sites open today",
        "today_h": "Open today",
        "today_note_one": "{n} location serving meals today.",
        "today_note_many": "{n} locations serving meals today.",
        "today_empty": "No sites are listed as open today. Check the full week "
                       "below, or some sites may not have reported their hours "
                       "yet.",
        "week_h": "Full week",
        "week_note": "All Anchorage-area sites, grouped by the days they serve.",
        "week_empty": "No weekly schedules are available right now.",
        "varies_h": "Other sites (call for days)",
        "varies_note": "These sites are active but didn’t list clear weekly "
                       "days — check the note or call to confirm.",
        "soon_h": "Opening soon",
        "soon_starts": "starts",
        "open_label": "Open:",
        "dates_label": "Dates:",
        "call": "Call",
        "directions": "Directions",
        "foot_doublecheck_strong": "Always good to double-check.",
        "foot_doublecheck": "Sites are added and updated through the summer, "
                            "and hours can change. This page is rebuilt "
                            "automatically from the USDA data feed.",
        "foot_official": "Official map: {finder}. Report a wrong listing to "
                         "{agency}.",
        "foot_help": "Need more help? Call the USDA National Hunger Hotline at "
                     "{phone} (Mon–Fri, 7 a.m.–7 p.m. "
                     "Alaska time).",
        "foot_source": "Data source: USDA Food and Nutrition Service. This is a "
                       "community-built page and is not an official USDA "
                       "website.",
        "a11y_h": "Accessibility",
        "a11y_text": "We want this page to work for everyone. It aims to meet "
                     "WCAG 2.1 AA. If you hit an accessibility barrier, please "
                     "tell us so we can fix it.",
        "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
                 "Saturday", "Sunday"],
        "days_abbr": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
        "meals": {"Breakfast": "Breakfast", "Lunch": "Lunch",
                  "Morning snack": "Morning snack",
                  "Afternoon snack": "Afternoon snack", "Dinner": "Dinner"},
        "models": {"Eat on-site": "Eat on-site",
                   "Grab & go / pick-up": "Grab & go / pick-up"},
    },

    "es": {
        "html_lang": "es",
        "review_note": "Esta traducción es automática y está "
                       "pendiente de revisión por una persona. Si algo no "
                       "queda claro, consulte la versión en inglés.",
        "title": "Comidas de verano gratis en Anchorage",
        "meta_desc": "Comidas de verano gratuitas para niños y jóvenes "
                     "de 18 años o menos en Anchorage, Alaska. Vea los "
                     "lugares abiertos hoy y durante la semana.",
        "skip": "Saltar a las comidas de hoy",
        "h1": "Comidas de verano gratis en Anchorage",
        "sub": "Desayuno, almuerzo y meriendas gratis para cualquier persona "
               "de 18 años o menos. Sin inscripción, sin "
               "identificación y sin costo.",
        "lang_label": "Idioma",
        "updated": "Actualizado",
        "open_today_one": "{n} lugar abierto hoy",
        "open_today_many": "{n} lugares abiertos hoy",
        "today_h": "Abierto hoy",
        "today_note_one": "{n} lugar sirve comidas hoy.",
        "today_note_many": "{n} lugares sirven comidas hoy.",
        "today_empty": "No hay lugares indicados como abiertos hoy. Consulte la "
                       "semana completa más abajo; es posible que algunos "
                       "lugares aún no hayan informado su horario.",
        "week_h": "Semana completa",
        "week_note": "Todos los lugares del área de Anchorage, agrupados "
                     "por los días en que sirven.",
        "week_empty": "No hay horarios semanales disponibles en este momento.",
        "varies_h": "Otros lugares (llame para conocer los días)",
        "varies_note": "Estos lugares están activos pero no indicaron "
                       "días semanales claros: consulte la nota o llame "
                       "para confirmar.",
        "soon_h": "Próximos a abrir",
        "soon_starts": "comienza",
        "open_label": "Abierto:",
        "dates_label": "Fechas:",
        "call": "Llamar",
        "directions": "Cómo llegar",
        "foot_doublecheck_strong": "Siempre conviene confirmar.",
        "foot_doublecheck": "Se agregan y actualizan lugares durante el verano, "
                            "y los horarios pueden cambiar. Esta página se "
                            "actualiza automáticamente con los datos del "
                            "USDA.",
        "foot_official": "Mapa oficial: {finder}. Informe un dato incorrecto a "
                         "{agency}.",
        "foot_help": "¿Necesita más ayuda? Llame a la Línea "
                     "Nacional contra el Hambre del USDA al {phone} (lunes a "
                     "viernes, de 7 a.m. a 7 p.m., hora de Alaska).",
        "foot_source": "Fuente de datos: Servicio de Alimentos y Nutrición "
                       "del USDA. Esta es una página creada por la "
                       "comunidad y no es un sitio oficial del USDA.",
        "a11y_h": "Accesibilidad",
        "a11y_text": "Queremos que esta página funcione para todos. Busca "
                     "cumplir con WCAG 2.1 AA. Si encuentra una barrera de "
                     "accesibilidad, avísenos para poder corregirla.",
        "days": ["lunes", "martes", "miércoles", "jueves", "viernes",
                 "sábado", "domingo"],
        "days_abbr": ["lun", "mar", "mié", "jue", "vie", "sáb", "dom"],
        "meals": {"Breakfast": "Desayuno", "Lunch": "Almuerzo",
                  "Morning snack": "Merienda de la mañana",
                  "Afternoon snack": "Merienda de la tarde", "Dinner": "Cena"},
        "models": {"Eat on-site": "Comer en el lugar",
                   "Grab & go / pick-up": "Para llevar / recoger"},
    },

    "hmn": {
        "html_lang": "hmn",
        "review_note": "Cov lus txhais no yog siv tshuab txhais thiab tseem tos "
                       "kom ib tug neeg tshuaj xyuas. Yog tsis meej, thov saib "
                       "cov ua lus Askiv.",
        "title": "Pluas Noj Caij Ntuj Sov Pub Dawb hauv Anchorage",
        "meta_desc": "Pluas noj caij ntuj sov pub dawb rau cov menyuam hnub "
                     "nyoog 18 xyoo rov hauv hauv Anchorage, Alaska. Saib cov "
                     "chaw qhib hnub no thiab tag nrho lub lim tiam.",
        "skip": "Hla mus rau cov pluas noj hnub no",
        "h1": "Pluas Noj Caij Ntuj Sov Pub Dawb hauv Anchorage",
        "sub": "Pub dawb tshais, su, thiab khoom noj txom rau txhua tus hnub "
               "nyoog 18 xyoo rov hauv. Tsis txhob sau npe, tsis xav tau ID, "
               "thiab tsis muaj nqi.",
        "lang_label": "Hom lus",
        "updated": "Hloov tshiab",
        "open_today_one": "{n} qhov chaw qhib hnub no",
        "open_today_many": "{n} qhov chaw qhib hnub no",
        "today_h": "Qhib hnub no",
        "today_note_one": "{n} qhov chaw muab pluas noj hnub no.",
        "today_note_many": "{n} qhov chaw muab pluas noj hnub no.",
        "today_empty": "Tsis muaj chaw teev tseg tias qhib hnub no. Saib tag "
                       "nrho lub lim tiam hauv qab, lossis tej zaum qee qhov "
                       "chaw tseem tsis tau qhia lawv lub sijhawm.",
        "week_h": "Tag nrho lub lim tiam",
        "week_note": "Tag nrho cov chaw hauv cheeb tsam Anchorage, muab faib "
                     "raws li hnub lawv muab noj.",
        "week_empty": "Tsis muaj sijhawm lub lim tiam tam sim no.",
        "varies_h": "Lwm qhov chaw (hu xov tooj rau hnub)",
        "varies_note": "Cov chaw no tseem ua haujlwm tab sis tsis tau teev hnub "
                       "lub lim tiam meej — saib cov ntawv ceeb toom lossis "
                       "hu xov tooj kom paub tseeb.",
        "soon_h": "Yuav qhib sai sai",
        "soon_starts": "pib",
        "open_label": "Qhib:",
        "dates_label": "Hnub:",
        "call": "Hu",
        "directions": "Kev taw qhia",
        "foot_doublecheck_strong": "Ib txwm zoo los kuaj dua.",
        "foot_doublecheck": "Muab ntxiv thiab hloov cov chaw thoob plaws lub "
                            "caij ntuj sov, thiab lub sijhawm hloov tau. Nplooj "
                            "ntawv no rov tsim los ntawm USDA cov ntaub ntawv.",
        "foot_official": "Daim ntawv qhia chaw raug cai: {finder}. Qhia qhov "
                         "teev tsis raug rau {agency}.",
        "foot_help": "Xav tau kev pab ntxiv? Hu rau USDA National Hunger "
                     "Hotline ntawm {phone} (Monday–Friday, "
                     "7 a.m.–7 p.m., sijhawm Alaska).",
        "foot_source": "Qhov chaw muab ntaub ntawv: USDA Food and Nutrition "
                       "Service. Nplooj ntawv no yog tsim los ntawm zej zog "
                       "thiab tsis yog USDA lub vev xaib raug cai.",
        "a11y_h": "Kev nkag tau yooj yim",
        "a11y_text": "Peb xav kom nplooj ntawv no siv tau rau txhua tus. Yog "
                     "koj pom ib qho teeb meem nkag tau, thov qhia rau peb kom "
                     "peb kho tau.",
        # Day names kept in English for Hmong pending a native-speaker review
        # (Hmong weekday terms vary by community); flagged by the review banner.
        "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
                 "Saturday", "Sunday"],
        "days_abbr": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
        "meals": {"Breakfast": "Tshais", "Lunch": "Su",
                  "Morning snack": "Khoom noj txom sawv ntxov",
                  "Afternoon snack": "Khoom noj txom tav su", "Dinner": "Hmo"},
        "models": {"Eat on-site": "Noj ntawm qhov chaw",
                   "Grab & go / pick-up": "Nqa mus / tos txais"},
    },

    "sm": {
        "html_lang": "sm",
        "review_note": "O lenei faaliliuga na faia e se masini ma o loo "
                       "faatali mo se toe iloiloga a se tagata. Afai e le "
                       "manino, faamolemole vaai i le gagana Peretania.",
        "title": "Taumafa Fua o le Taumafanafana i Anchorage",
        "meta_desc": "Taumafa fua o le taumafanafana mo tamaiti e 18 tausaga ma "
                     "lalo i Anchorage, Alaska. Vaai i nofoaga e tatala i le "
                     "aso ma le vaiaso atoa.",
        "skip": "Oso i taumafa o le aso",
        "h1": "Taumafa Fua o le Taumafanafana i Anchorage",
        "sub": "Taeao, aoauli, ma meaai mama e fua mo so o se tasi e 18 tausaga "
               "ma lalo. E leai se resitala, e leai se ID, ma e leai se totogi.",
        "lang_label": "Gagana",
        "updated": "Faafouina",
        "open_today_one": "{n} nofoaga e tatala i le aso",
        "open_today_many": "{n} nofoaga e tatala i le aso",
        "today_h": "Tatala i le aso",
        "today_note_one": "{n} nofoaga o loo tuuina atu taumafa i le aso.",
        "today_note_many": "{n} nofoaga o loo tuuina atu taumafa i le aso.",
        "today_empty": "E leai ni nofoaga o loo lisiina e tatala i le aso. "
                       "Vaai i le vaiaso atoa i lalo, atonu o nisi nofoaga e "
                       "lei lipotia o latou itula.",
        "week_h": "Vaiaso atoa",
        "week_note": "O nofoaga uma i le eria o Anchorage, vaevaeina e tusa ai "
                     "ma aso latou te tuuina atu ai taumafa.",
        "week_empty": "E leai ni faasologa o le vaiaso o loo maua i le taimi "
                      "nei.",
        "varies_h": "Isi nofoaga (telefoni mo aso)",
        "varies_note": "O loo galulue nei nofoaga ae lei lisiina manino aso o "
                       "le vaiaso — vaai i le faamatalaga pe telefoni e "
                       "faamautu.",
        "soon_h": "O le a tatala lata mai",
        "soon_starts": "amata",
        "open_label": "Tatala:",
        "dates_label": "Aso:",
        "call": "Telefoni",
        "directions": "Faatonuga",
        "foot_doublecheck_strong": "E lelei lava le toe siaki.",
        "foot_doublecheck": "E faaopoopo ma faafou nofoaga i le taumafanafana "
                            "atoa, ma e mafai ona suia itula. O lenei itulau e "
                            "toe fausia otometi mai faamaumauga a le USDA.",
        "foot_official": "Faafanua aloaia: {finder}. Lipoti se lisi sese i le "
                         "{agency}.",
        "foot_help": "E te manaomia se isi fesoasoani? Telefoni i le USDA "
                     "National Hunger Hotline i le {phone} (Aso Gafua–Aso "
                     "Faraile, 7 a.m.–7 p.m., taimi o Alaska).",
        "foot_source": "Puna o faamaumauga: USDA Food and Nutrition Service. O "
                       "se itulau na faia e le faalapotopotoga ma e le o se "
                       "upega tafailagi aloaia a le USDA.",
        "a11y_h": "Avanoa faafaigofie",
        "a11y_text": "Matou te manao ia aoga lenei itulau mo tagata uma. Afai "
                     "e te maua se faalavelave i le avanoa, faafesootai mai ia "
                     "matou ina ia mafai ona faasai.",
        "days": ["Aso Gafua", "Aso Lua", "Aso Lulu", "Aso Tofi", "Aso Faraile",
                 "Aso Toonai", "Aso Sa"],
        "days_abbr": ["Gaf", "Lua", "Lul", "Tof", "Far", "Too", "Sa"],
        "meals": {"Breakfast": "Taeao", "Lunch": "Aoauli",
                  "Morning snack": "Meaai taeao",
                  "Afternoon snack": "Meaai aoauli", "Dinner": "Afiafi"},
        "models": {"Eat on-site": "Ai i le nofoaga",
                   "Grab & go / pick-up": "Ave ese / piki"},
    },

    "tl": {
        "html_lang": "tl",
        "review_note": "Awtomatiko ang pagsasaling ito at naghihintay pa ng "
                       "rebyu ng tao. Kung may hindi malinaw, pakitingnan ang "
                       "bersyong Ingles.",
        "title": "Libreng Pagkain sa Tag-init sa Anchorage",
        "meta_desc": "Libreng pagkain sa tag-init para sa mga batang 18 anyos "
                     "pababa sa Anchorage, Alaska. Tingnan ang mga lugar na "
                     "bukas ngayon at buong linggo.",
        "skip": "Lumaktaw sa pagkain ngayong araw",
        "h1": "Libreng Pagkain sa Tag-init sa Anchorage",
        "sub": "Libreng almusal, tanghalian, at meryenda para sa sinumang 18 "
               "anyos pababa. Walang pagpaparehistro, walang ID, at walang "
               "bayad.",
        "lang_label": "Wika",
        "updated": "Na-update",
        "open_today_one": "{n} lugar na bukas ngayon",
        "open_today_many": "{n} (na) lugar na bukas ngayon",
        "today_h": "Bukas ngayon",
        "today_note_one": "{n} lugar ang naghahain ng pagkain ngayon.",
        "today_note_many": "{n} (na) lugar ang naghahain ng pagkain ngayon.",
        "today_empty": "Walang nakalistang lugar na bukas ngayon. Tingnan ang "
                       "buong linggo sa ibaba, o maaaring hindi pa naiulat ng "
                       "ilang lugar ang kanilang oras.",
        "week_h": "Buong linggo",
        "week_note": "Lahat ng lugar sa lugar ng Anchorage, nakagrupo ayon sa "
                     "mga araw na naghahain sila.",
        "week_empty": "Walang available na lingguhang iskedyul sa ngayon.",
        "varies_h": "Iba pang lugar (tumawag para sa mga araw)",
        "varies_note": "Aktibo ang mga lugar na ito ngunit hindi naglista ng "
                       "malinaw na lingguhang araw — tingnan ang tala o "
                       "tumawag para makumpirma.",
        "soon_h": "Malapit nang magbukas",
        "soon_starts": "magsisimula",
        "open_label": "Bukas:",
        "dates_label": "Mga petsa:",
        "call": "Tumawag",
        "directions": "Direksyon",
        "foot_doublecheck_strong": "Laging mabuting tiyakin.",
        "foot_doublecheck": "Nagdaragdag at nag-a-update ng mga lugar sa buong "
                            "tag-init, at maaaring magbago ang oras. "
                            "Awtomatikong muling binubuo ang pahinang ito mula "
                            "sa datos ng USDA.",
        "foot_official": "Opisyal na mapa: {finder}. Iulat ang maling listing "
                         "sa {agency}.",
        "foot_help": "Kailangan ng karagdagang tulong? Tumawag sa USDA "
                     "National Hunger Hotline sa {phone} (Lunes–Biyernes, "
                     "7 a.m.–7 p.m., oras ng Alaska).",
        "foot_source": "Pinagmulan ng datos: USDA Food and Nutrition Service. "
                       "Ito ay pahinang gawa ng komunidad at hindi opisyal na "
                       "website ng USDA.",
        "a11y_h": "Accessibility",
        "a11y_text": "Gusto naming gumana ang pahinang ito para sa lahat. "
                     "Layunin nitong matugunan ang WCAG 2.1 AA. Kung makakita "
                     "ka ng hadlang sa accessibility, sabihin sa amin para "
                     "maayos namin.",
        "days": ["Lunes", "Martes", "Miyerkules", "Huwebes", "Biyernes",
                 "Sabado", "Linggo"],
        "days_abbr": ["Lun", "Mar", "Miy", "Huw", "Biy", "Sab", "Lin"],
        "meals": {"Breakfast": "Almusal", "Lunch": "Tanghalian",
                  "Morning snack": "Meryenda sa umaga",
                  "Afternoon snack": "Meryenda sa hapon", "Dinner": "Hapunan"},
        "models": {"Eat on-site": "Kumain sa lugar",
                   "Grab & go / pick-up": "Pakuha / pick-up"},
    },
}
