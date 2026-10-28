"""V1.19 reviewed unlanded Romanian workshop/craft vocabulary proposal; owner reviews, applies and lands later."""
from basic_words_v33_data import BEGINNER_BENCHMARK as BEGINNER_BENCHMARK
from weather_and_landscape_v1_13_data import DEFERRED_AMBIGUOUS_TERMS as DEFERRED_AMBIGUOUS_TERMS

BUILD_VERSION = 'fixture-v1-19-tools-and-crafts'

LANDING_STATUS = 'not_landed'

HANDOFF_STATUS = 'owner_review_later'

WORK_MODE = 'reviewed-pool'

NOTE = ('Reviewed Romanian workshop,craft and everyday vocabulary source pool;owner reviews,applies and '
 'lands later. No serving fixtures,boards,targets,recipes,routes or runtime approval.')

GAME_ITEM_IDS = ()

INTUITIVE_PAIRS = ()

PROPOSED_ITEM_IDS = ('v119-diblu',
 'v119-pila',
 'v119-rindea',
 'v119-dalta',
 'v119-burghiu',
 'v119-bormasina',
 'v119-mistrie',
 'v119-ruleta',
 'v119-topor',
 'v119-baros',
 'v119-nicovala',
 'v119-menghina',
 'v119-adeziv',
 'v119-banda_adeziva',
 'v119-teava',
 'v119-tigla',
 'v119-caramida',
 'v119-mortar',
 'v119-ciment',
 'v119-beton',
 'v119-tencuiala',
 'v119-var',
 'v119-scandura',
 'v119-placaj',
 'v119-sipca',
 'v119-degetar',
 'v119-croseta',
 'v119-ghem',
 'v119-croitor',
 'v119-tamplar',
 'v119-fierar',
 'v119-zidar',
 'v119-instalator',
 'v119-electrician',
 'v119-atelier',
 'v119-trusa',
 'v119-unealta',
 'v119-masina_de_cusut',
 'v119-andrele',
 'v119-panglica',
 'v119-petic',
 'v119-cusatura',
 'v119-tiv',
 'v119-broderie',
 'v119-ciocan',
 'v119-surub',
 'v119-fierastrau',
 'v119-cleste',
 'v119-surubelnita')

HELD_ITEM_IDS = ('v119-piulita',
 'v119-saiba',
 'v119-smirghel',
 'v119-boloboc',
 'v119-harlet',
 'v119-tarnacop',
 'v119-secera',
 'v119-coasa',
 'v119-ranga',
 'v119-gips',
 'v119-trafalet')

NEW_NODE_IDS = ('n_v1_19_diblu',
 'n_v1_19_pila',
 'n_v1_19_rindea',
 'n_v1_19_dalta',
 'n_v1_19_burghiu',
 'n_v1_19_bormasina',
 'n_v1_19_mistrie',
 'n_v1_19_ruleta',
 'n_v1_19_topor',
 'n_v1_19_baros',
 'n_v1_19_nicovala',
 'n_v1_19_menghina',
 'n_v1_19_adeziv',
 'n_v1_19_banda_adeziva',
 'n_v1_19_teava',
 'n_v1_19_tigla',
 'n_v1_19_caramida',
 'n_v1_19_mortar',
 'n_v1_19_ciment',
 'n_v1_19_beton',
 'n_v1_19_tencuiala',
 'n_v1_19_var',
 'n_v1_19_scandura',
 'n_v1_19_placaj',
 'n_v1_19_sipca',
 'n_v1_19_degetar',
 'n_v1_19_croseta',
 'n_v1_19_ghem',
 'n_v1_19_croitor',
 'n_v1_19_tamplar',
 'n_v1_19_fierar',
 'n_v1_19_zidar',
 'n_v1_19_instalator',
 'n_v1_19_electrician',
 'n_v1_19_atelier',
 'n_v1_19_trusa',
 'n_v1_19_unealta',
 'n_v1_19_masina_de_cusut',
 'n_v1_19_andrele',
 'n_v1_19_panglica',
 'n_v1_19_petic',
 'n_v1_19_cusatura',
 'n_v1_19_tiv',
 'n_v1_19_broderie')

NODES = ({'id': 'n_v1_19_diblu',
  'node_type': 'concept',
  'label_ro': 'Diblu',
  'category': 'viata_de_roman',
  'description': 'Piesă introdusă într-o gaură din zidărie pentru fixarea unui cui sau șurub.',
  'salience': 0.72,
  'aliases': ['diblul', 'dibluri', 'diblurile', 'diblului', 'diblurilor']},
 {'id': 'n_v1_19_pila',
  'node_type': 'concept',
  'label_ro': 'Pilă',
  'category': 'viata_de_roman',
  'description': 'Unealtă din oțel, cu numeroși dinți mărunți, folosită la ajustarea pieselor.',
  'salience': 0.72,
  'aliases': ['pile', 'pilele', 'pilei', 'pilelor']},
 {'id': 'n_v1_19_rindea',
  'node_type': 'concept',
  'label_ro': 'Rindea',
  'category': 'viata_de_roman',
  'description': 'Unealtă cu cuțit, folosită la netezirea și fasonarea suprafețelor din lemn.',
  'salience': 0.72,
  'aliases': ['rindeaua', 'rindele', 'rindelele', 'rindelei', 'rindelelor']},
 {'id': 'n_v1_19_dalta',
  'node_type': 'concept',
  'label_ro': 'Daltă',
  'category': 'viata_de_roman',
  'description': 'Unealtă cu tăiș în formă de pană, folosită la cioplit, scobit sau tăiat.',
  'salience': 0.72,
  'aliases': ['dălți', 'dălțile', 'dălții', 'dălților']},
 {'id': 'n_v1_19_burghiu',
  'node_type': 'concept',
  'label_ro': 'Burghiu',
  'category': 'viata_de_roman',
  'description': 'Unealtă de oțel, adesea spiralată, care execută găuri prin rotire.',
  'salience': 0.72,
  'aliases': ['burghiul', 'burghie', 'burghiele', 'burghiului', 'burghielor']},
 {'id': 'n_v1_19_bormasina',
  'node_type': 'concept',
  'label_ro': 'Bormașină',
  'category': 'viata_de_roman',
  'description': 'Mașină care execută găuri în materiale cu ajutorul unui burghiu rotitor.',
  'salience': 0.72,
  'aliases': ['bormașini',
              'bormașinile',
              'bormașinii',
              'bormașinilor',
              'mașină de găurit',
              'mașini de găurit',
              'mașinile de găurit',
              'mașinii de găurit',
              'mașinilor de găurit']},
 {'id': 'n_v1_19_mistrie',
  'node_type': 'concept',
  'label_ro': 'Mistrie',
  'category': 'viata_de_roman',
  'description': 'Unealtă de zidărie cu lamă și mâner, folosită pentru întinderea mortarului.',
  'salience': 0.72,
  'aliases': ['mistria', 'mistrii', 'mistriile', 'mistriei', 'mistriilor']},
 {'id': 'n_v1_19_ruleta',
  'node_type': 'concept',
  'label_ro': 'Ruletă',
  'category': 'viata_de_roman',
  'description': 'Instrument de măsurat lungimi, cu o bandă gradată care se strânge prin rulare.',
  'salience': 0.72,
  'aliases': ['rulete', 'ruletele', 'ruletei', 'ruletelor']},
 {'id': 'n_v1_19_topor',
  'node_type': 'concept',
  'label_ro': 'Topor',
  'category': 'viata_de_roman',
  'description': 'Unealtă cu coadă și tăiș de oțel, pentru tăiat sau despicat lemnul.',
  'salience': 0.72,
  'aliases': ['toporul', 'topoare', 'topoarele', 'toporului', 'topoarelor']},
 {'id': 'n_v1_19_baros',
  'node_type': 'concept',
  'label_ro': 'Baros',
  'category': 'viata_de_roman',
  'description': 'Ciocan mare și greu, folosit la lucrări care cer lovituri puternice.',
  'salience': 0.72,
  'aliases': ['barosul', 'baroase', 'baroasele', 'barosului', 'baroaselor']},
 {'id': 'n_v1_19_nicovala',
  'node_type': 'concept',
  'label_ro': 'Nicovală',
  'category': 'viata_de_roman',
  'description': 'Suport de oțel sau fontă pe care se prelucrează piese de metal prin lovire.',
  'salience': 0.72,
  'aliases': ['nicovale', 'nicovalele', 'nicovalei', 'nicovalelor']},
 {'id': 'n_v1_19_menghina',
  'node_type': 'concept',
  'label_ro': 'Menghină',
  'category': 'viata_de_roman',
  'description': 'Dispozitiv cu două fălci apropiate cu un șurub, pentru fixarea pieselor de '
                 'lucru.',
  'salience': 0.72,
  'aliases': ['menghine', 'menghinele', 'menghinei', 'menghinelor']},
 {'id': 'n_v1_19_adeziv',
  'node_type': 'concept',
  'label_ro': 'Adeziv',
  'category': 'viata_de_roman',
  'description': 'Substanță cu care se lipesc suprafețe.',
  'salience': 0.72,
  'aliases': ['adezivul', 'adezivi', 'adezivii', 'adezivului', 'adezivilor']},
 {'id': 'n_v1_19_banda_adeziva',
  'node_type': 'concept',
  'label_ro': 'Bandă adezivă',
  'category': 'viata_de_roman',
  'description': 'Fâșie cu adeziv folosită pentru lipire, fixare ori ambalare.',
  'salience': 0.72,
  'aliases': ['benzi adezive', 'benzile adezive', 'benzii adezive', 'benzilor adezive']},
 {'id': 'n_v1_19_teava',
  'node_type': 'concept',
  'label_ro': 'Țeavă',
  'category': 'viata_de_roman',
  'description': 'Tub lung și gol în interior, folosit în instalații.',
  'salience': 0.72,
  'aliases': ['țevi', 'țevile', 'țevii', 'țevilor']},
 {'id': 'n_v1_19_tigla',
  'node_type': 'concept',
  'label_ro': 'Țiglă',
  'category': 'viata_de_roman',
  'description': 'Placă folosită la învelirea acoperișului unei case.',
  'salience': 0.72,
  'aliases': ['țigle', 'țiglele', 'țiglei', 'țiglelor']},
 {'id': 'n_v1_19_caramida',
  'node_type': 'concept',
  'label_ro': 'Cărămidă',
  'category': 'viata_de_roman',
  'description': 'Piesă de construcție folosită la ziduri și clădiri.',
  'salience': 0.72,
  'aliases': ['cărămizi', 'cărămizile', 'cărămizii', 'cărămizilor']},
 {'id': 'n_v1_19_mortar',
  'node_type': 'concept',
  'label_ro': 'Mortar',
  'category': 'viata_de_roman',
  'description': 'Amestec folosit la legarea elementelor unei zidării.',
  'salience': 0.72,
  'aliases': ['mortarul', 'mortare', 'mortarele', 'mortarului', 'mortarelor']},
 {'id': 'n_v1_19_ciment',
  'node_type': 'concept',
  'label_ro': 'Ciment',
  'category': 'viata_de_roman',
  'description': 'Pulbere folosită ca liant în mortare și betoane.',
  'salience': 0.72,
  'aliases': ['cimentul', 'cimenturi', 'cimenturile', 'cimentului', 'cimenturilor']},
 {'id': 'n_v1_19_beton',
  'node_type': 'concept',
  'label_ro': 'Beton',
  'category': 'viata_de_roman',
  'description': 'Material de construcție obținut din liant, apă și agregate.',
  'salience': 0.72,
  'aliases': ['betonul', 'betoane', 'betoanele', 'betonului', 'betoanelor']},
 {'id': 'n_v1_19_tencuiala',
  'node_type': 'concept',
  'label_ro': 'Tencuială',
  'category': 'viata_de_roman',
  'description': 'Strat de mortar care acoperă un zid sau un tavan.',
  'salience': 0.72,
  'aliases': ['tencuieli', 'tencuielile', 'tencuielii', 'tencuielilor']},
 {'id': 'n_v1_19_var',
  'node_type': 'concept',
  'label_ro': 'Var',
  'category': 'viata_de_roman',
  'description': 'Material folosit ca liant și la văruirea pereților.',
  'salience': 0.72,
  'aliases': ['varul', 'varuri', 'varurile', 'varului', 'varurilor']},
 {'id': 'n_v1_19_scandura',
  'node_type': 'concept',
  'label_ro': 'Scândură',
  'category': 'viata_de_roman',
  'description': 'Piesă lată de lemn obținută prin tăierea trunchiului.',
  'salience': 0.72,
  'aliases': ['scânduri', 'scândurile', 'scândurii', 'scândurilor']},
 {'id': 'n_v1_19_placaj',
  'node_type': 'concept',
  'label_ro': 'Placaj',
  'category': 'viata_de_roman',
  'description': 'Placă realizată din straturi subțiri de lemn lipite între ele.',
  'salience': 0.72,
  'aliases': ['placajul', 'placaje', 'placajele', 'placajului', 'placajelor']},
 {'id': 'n_v1_19_sipca',
  'node_type': 'concept',
  'label_ro': 'Șipcă',
  'category': 'viata_de_roman',
  'description': 'Scândură lungă și îngustă folosită în tâmplărie ori dulgherie.',
  'salience': 0.72,
  'aliases': ['șipci', 'șipcile', 'șipcii', 'șipcilor']},
 {'id': 'n_v1_19_degetar',
  'node_type': 'concept',
  'label_ro': 'Degetar',
  'category': 'viata_de_roman',
  'description': 'Căpăcel care se poartă pe deget la cusut.',
  'salience': 0.72,
  'aliases': ['degetarul', 'degetare', 'degetarele', 'degetarului', 'degetarelor']},
 {'id': 'n_v1_19_croseta',
  'node_type': 'concept',
  'label_ro': 'Croșetă',
  'category': 'viata_de_roman',
  'description': 'Ac cu vârful îndoit ca un cârlig, folosit la croșetat.',
  'salience': 0.72,
  'aliases': ['croșete', 'croșetele', 'croșetei', 'croșetelor']},
 {'id': 'n_v1_19_ghem',
  'node_type': 'concept',
  'label_ro': 'Ghem',
  'category': 'viata_de_roman',
  'description': 'Fire de ață ori de lână înfășurate într-o formă aproximativ rotundă.',
  'salience': 0.72,
  'aliases': ['ghemul', 'gheme', 'ghemele', 'ghemului', 'ghemelor']},
 {'id': 'n_v1_19_croitor',
  'node_type': 'concept',
  'label_ro': 'Croitor',
  'category': 'societate',
  'description': 'Meseriaș care croiește, coase ori repară haine.',
  'salience': 0.72,
  'aliases': ['croitorul', 'croitori', 'croitorii', 'croitorului', 'croitorilor']},
 {'id': 'n_v1_19_tamplar',
  'node_type': 'concept',
  'label_ro': 'Tâmplar',
  'category': 'societate',
  'description': 'Meseriaș care face mobilă și alte obiecte din lemn.',
  'salience': 0.72,
  'aliases': ['tâmplarul', 'tâmplari', 'tâmplarii', 'tâmplarului', 'tâmplarilor']},
 {'id': 'n_v1_19_fierar',
  'node_type': 'concept',
  'label_ro': 'Fierar',
  'category': 'societate',
  'description': 'Meseriaș care prelucrează fierul și alte metale.',
  'salience': 0.72,
  'aliases': ['fierarul', 'fierari', 'fierarii', 'fierarului', 'fierarilor']},
 {'id': 'n_v1_19_zidar',
  'node_type': 'concept',
  'label_ro': 'Zidar',
  'category': 'societate',
  'description': 'Meseriaș care execută lucrări de zidărie.',
  'salience': 0.72,
  'aliases': ['zidarul', 'zidari', 'zidarii', 'zidarului', 'zidarilor']},
 {'id': 'n_v1_19_instalator',
  'node_type': 'concept',
  'label_ro': 'Instalator',
  'category': 'societate',
  'description': 'Meseriaș care montează și repară instalații tehnico-sanitare.',
  'salience': 0.72,
  'aliases': ['instalatorul', 'instalatori', 'instalatorii', 'instalatorului', 'instalatorilor']},
 {'id': 'n_v1_19_electrician',
  'node_type': 'concept',
  'label_ro': 'Electrician',
  'category': 'societate',
  'description': 'Meseriaș care lucrează la instalații și aparate electrice.',
  'salience': 0.72,
  'aliases': ['electricianul',
              'electricieni',
              'electricienii',
              'electricianului',
              'electricienilor']},
 {'id': 'n_v1_19_atelier',
  'node_type': 'concept',
  'label_ro': 'Atelier',
  'category': 'societate',
  'description': 'Spațiu înzestrat cu unelte ori mașini pentru muncă meșteșugărească sau '
                 'industrială.',
  'salience': 0.72,
  'aliases': ['atelierul', 'ateliere', 'atelierele', 'atelierului', 'atelierelor']},
 {'id': 'n_v1_19_trusa',
  'node_type': 'concept',
  'label_ro': 'Trusă',
  'category': 'viata_de_roman',
  'description': 'Ansamblu de instrumente păstrate într-o geantă sau cutie.',
  'salience': 0.72,
  'aliases': ['truse', 'trusele', 'trusei', 'truselor']},
 {'id': 'n_v1_19_unealta',
  'node_type': 'concept',
  'label_ro': 'Unealtă',
  'category': 'viata_de_roman',
  'description': 'Obiect ori dispozitiv cu care se execută o operație practică.',
  'salience': 0.72,
  'aliases': ['unelte', 'uneltele', 'uneltei', 'uneltelor']},
 {'id': 'n_v1_19_masina_de_cusut',
  'node_type': 'concept',
  'label_ro': 'Mașină de cusut',
  'category': 'viata_de_roman',
  'description': 'Mecanism cu care se realizează cusături pe materiale textile.',
  'salience': 0.72,
  'aliases': ['mașini de cusut', 'mașinile de cusut', 'mașinii de cusut', 'mașinilor de cusut']},
 {'id': 'n_v1_19_andrele',
  'node_type': 'concept',
  'label_ro': 'Andrele',
  'category': 'viata_de_roman',
  'description': 'Ace lungi și groase folosite la tricotatul manual.',
  'salience': 0.72,
  'aliases': ['andrea', 'andreaua', 'andrelele', 'andrelei', 'andrelelor']},
 {'id': 'n_v1_19_panglica',
  'node_type': 'concept',
  'label_ro': 'Panglică',
  'category': 'viata_de_roman',
  'description': 'Fâșie textilă îngustă folosită ca podoabă.',
  'salience': 0.72,
  'aliases': ['panglici', 'panglicile', 'panglicii', 'panglicilor']},
 {'id': 'n_v1_19_petic',
  'node_type': 'concept',
  'label_ro': 'Petic',
  'category': 'viata_de_roman',
  'description': 'Bucată de material cu care se poate repara o ruptură dintr-o haină.',
  'salience': 0.72,
  'aliases': ['peticul', 'petice', 'peticele', 'peticului', 'peticelor']},
 {'id': 'n_v1_19_cusatura',
  'node_type': 'concept',
  'label_ro': 'Cusătură',
  'category': 'viata_de_roman',
  'description': 'Îmbinare prin coasere a unor bucăți de material textil.',
  'salience': 0.72,
  'aliases': ['cusături', 'cusăturile', 'cusăturii', 'cusăturilor']},
 {'id': 'n_v1_19_tiv',
  'node_type': 'concept',
  'label_ro': 'Tiv',
  'category': 'viata_de_roman',
  'description': 'Margine de material textil îndoită și fixată prin cusătură.',
  'salience': 0.72,
  'aliases': ['tivul', 'tivuri', 'tivurile', 'tivului', 'tivurilor']},
 {'id': 'n_v1_19_broderie',
  'node_type': 'concept',
  'label_ro': 'Broderie',
  'category': 'viata_de_roman',
  'description': 'Ornament cusut cu fire pe un material textil.',
  'salience': 0.72,
  'aliases': ['broderia', 'broderii', 'broderiile', 'broderiei', 'broderiilor']})

EDGES = ({'src': 'n_v1_19_diblu',
  'dst': 'n_v32_workshop_fastener_surub',
  'relation': 'related_to',
  'label_ro': 'poate fixa un șurub într-o gaură',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_diblu',
  'dst': 'n_v24_home_structure_perete',
  'relation': 'related_to',
  'label_ro': 'poate fi introdus într-o gaură din perete',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_diblu',
  'dst': 'n_v1_3_material_lemn',
  'relation': 'related_to',
  'label_ro': 'poate fi o piesă din lemn',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_diblu',
  'dst': 'n_v4sti_metal',
  'relation': 'related_to',
  'label_ro': 'există dibluri metalice pentru fixare',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_pila',
  'dst': 'n_v4sti_metal',
  'relation': 'related_to',
  'label_ro': 'unealta poate fi confecționată din oțel',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_pila',
  'dst': 'n_v1_3_material_lemn',
  'relation': 'related_to',
  'label_ro': 'mânerul său poate fi din lemn',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_pila',
  'dst': 'n_v32_workshop_cut_fierastrau',
  'relation': 'related_to',
  'label_ro': 'o pilă de ascuțit poate prelucra dinții fierăstrăului',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_pila',
  'dst': 'n_v1_19_menghina',
  'relation': 'related_to',
  'label_ro': 'piesa pilită poate fi fixată într-o menghină',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_rindea',
  'dst': 'n_v1_3_material_lemn',
  'relation': 'related_to',
  'label_ro': 'netezește suprafețe din lemn',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_rindea',
  'dst': 'n_v1_19_scandura',
  'relation': 'related_to',
  'label_ro': 'poate netezi suprafața unei scânduri',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_rindea',
  'dst': 'n_v4sti_metal',
  'relation': 'related_to',
  'label_ro': 'unele modele au corp din metal',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_dalta',
  'dst': 'n_v1_3_material_lemn',
  'relation': 'related_to',
  'label_ro': 'o daltă de tâmplărie prelucrează lemnul',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_dalta',
  'dst': 'n_v4sti_metal',
  'relation': 'related_to',
  'label_ro': 'are o parte tăietoare din metal',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_dalta',
  'dst': 'n_sculptura',
  'relation': 'related_to',
  'label_ro': 'poate fi folosită la realizarea sculpturii',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_dalta',
  'dst': 'n_v32_workshop_hand_ciocan',
  'relation': 'related_to',
  'label_ro': 'unele dălți se folosesc prin lovire cu ciocanul',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_bormasina',
  'dst': 'n_v1_19_burghiu',
  'relation': 'related_to',
  'label_ro': 'poate roti un burghiu',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_burghiu',
  'dst': 'n_v4sti_metal',
  'relation': 'related_to',
  'label_ro': 'poate fi fabricat din metal',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_burghiu',
  'dst': 'n_v1_3_material_lemn',
  'relation': 'related_to',
  'label_ro': 'un burghiu pentru lemn execută găuri în lemn',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_burghiu',
  'dst': 'n_v24_home_structure_perete',
  'relation': 'related_to',
  'label_ro': 'un burghiu pentru zidărie execută găuri în perete',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_bormasina',
  'dst': 'n_v3sti_electricitate',
  'relation': 'related_to',
  'label_ro': 'modelele electrice folosesc electricitate',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_bormasina',
  'dst': 'n_v1_3_material_lemn',
  'relation': 'related_to',
  'label_ro': 'poate găuri lemnul cu un burghiu potrivit',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_bormasina',
  'dst': 'n_v24_home_structure_perete',
  'relation': 'related_to',
  'label_ro': 'poate găuri pereții cu un burghiu potrivit',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_mistrie',
  'dst': 'n_v1_19_mortar',
  'relation': 'related_to',
  'label_ro': 'întinde mortarul la zidărie',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_mistrie',
  'dst': 'n_v24_home_structure_perete',
  'relation': 'related_to',
  'label_ro': 'poate fi folosită la zidirea unui perete',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_mistrie',
  'dst': 'n_v1_3_material_lemn',
  'relation': 'related_to',
  'label_ro': 'mânerul său poate fi din lemn',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_mistrie',
  'dst': 'n_v4sti_metal',
  'relation': 'related_to',
  'label_ro': 'are o lamă din metal',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_ruleta',
  'dst': 'n_v24_school_supplies_rigla',
  'relation': 'related_to',
  'label_ro': 'măsoară lungimi, la fel ca rigla',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_ruleta',
  'dst': 'n_v24_home_structure_perete',
  'relation': 'related_to',
  'label_ro': 'poate măsura dimensiunile unui perete',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_ruleta',
  'dst': 'n_v24_home_surfaces_podea',
  'relation': 'related_to',
  'label_ro': 'poate măsura dimensiunile unei podele',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_ruleta',
  'dst': 'n_v4sti_metal',
  'relation': 'related_to',
  'label_ro': 'banda unor modele este din metal',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_topor',
  'dst': 'n_v4sti_metal',
  'relation': 'related_to',
  'label_ro': 'are o parte tăietoare din metal',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_topor',
  'dst': 'n_v1_3_material_lemn',
  'relation': 'related_to',
  'label_ro': 'poate tăia sau despica lemnul',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_topor',
  'dst': 'n_v32_workshop_cut_fierastrau',
  'relation': 'related_to',
  'label_ro': 'are în comun cu fierăstrăul tăierea lemnului',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_topor',
  'dst': 'n_v24_home_outdoor_gradina',
  'relation': 'related_to',
  'label_ro': 'poate fi folosit la lucrări cu lemnul în grădină',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_baros',
  'dst': 'n_v32_workshop_hand_ciocan',
  'relation': 'is_a',
  'label_ro': 'este un ciocan mare și greu',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 0},
 {'src': 'n_v1_19_baros',
  'dst': 'n_v4sti_metal',
  'relation': 'related_to',
  'label_ro': 'are un cap din metal',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_baros',
  'dst': 'n_v1_3_material_lemn',
  'relation': 'related_to',
  'label_ro': 'coada sa poate fi din lemn',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_baros',
  'dst': 'n_v28_nature_material_piatra',
  'relation': 'related_to',
  'label_ro': 'poate sparge piatra prin lovire',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_nicovala',
  'dst': 'n_v4sti_metal',
  'relation': 'related_to',
  'label_ro': 'pe ea se pot prelucra piese din metal',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_nicovala',
  'dst': 'n_v32_workshop_hand_ciocan',
  'relation': 'related_to',
  'label_ro': 'susține piesa lovită cu ciocanul',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_fierar',
  'dst': 'n_v1_19_nicovala',
  'relation': 'related_to',
  'label_ro': 'poate prelucra piesa pe nicovală',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_nicovala',
  'dst': 'n_v32_workshop_hand_cleste',
  'relation': 'related_to',
  'label_ro': 'piesa de pe nicovală poate fi ținută cu un clește',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_menghina',
  'dst': 'n_v4sti_metal',
  'relation': 'related_to',
  'label_ro': 'poate fixa piese din metal',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_menghina',
  'dst': 'n_v1_3_material_lemn',
  'relation': 'related_to',
  'label_ro': 'poate fixa piese din lemn',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_menghina',
  'dst': 'n_v32_workshop_cut_fierastrau',
  'relation': 'related_to',
  'label_ro': 'poate ține piesa în timpul tăierii cu fierăstrăul',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_11_lipici',
  'dst': 'n_v1_19_adeziv',
  'relation': 'is_a',
  'label_ro': 'este o substanță adezivă',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 0},
 {'src': 'n_v1_19_adeziv',
  'dst': 'n_v1_3_material_lemn',
  'relation': 'related_to',
  'label_ro': 'există adezivi pentru lipirea lemnului',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_adeziv',
  'dst': 'n_v1_11_sticla',
  'relation': 'related_to',
  'label_ro': 'există adezivi pentru lipirea sticlei',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_adeziv',
  'dst': 'n_v1_11_cauciuc',
  'relation': 'related_to',
  'label_ro': 'există adezivi pentru lipirea cauciucului',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_banda_adeziva',
  'dst': 'n_v1_19_adeziv',
  'relation': 'related_to',
  'label_ro': 'are un strat de adeziv',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_banda_adeziva',
  'dst': 'n_v1_11_hartie',
  'relation': 'related_to',
  'label_ro': 'poate avea suport din hârtie',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_banda_adeziva',
  'dst': 'n_v1_11_cutie',
  'relation': 'related_to',
  'label_ro': 'poate închide o cutie pentru ambalare',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_banda_adeziva',
  'dst': 'n_v1_11_foarfeca',
  'relation': 'related_to',
  'label_ro': 'poate fi tăiată cu foarfeca',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_teava',
  'dst': 'n_v4sti_metal',
  'relation': 'related_to',
  'label_ro': 'poate fi fabricată din metal',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_teava',
  'dst': 'n_v33_bathroom_fixture_robinet',
  'relation': 'related_to',
  'label_ro': 'poate fi legată la un robinet',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_teava',
  'dst': 'n_v24_home_structure_perete',
  'relation': 'related_to',
  'label_ro': 'poate traversa un perete într-o instalație',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_teava',
  'dst': 'n_v32_workshop_hand_cleste',
  'relation': 'related_to',
  'label_ro': 'poate fi prinsă cu un clește pentru țevi',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_tigla',
  'dst': 'n_v24_home_structure_acoperis',
  'relation': 'part_of',
  'label_ro': 'poate face parte din învelitoarea acoperișului',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 0},
 {'src': 'n_v1_19_tigla',
  'dst': 'n_v4soc_casa',
  'relation': 'related_to',
  'label_ro': 'poate acoperi o casă',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_tigla',
  'dst': 'n_v1_3_material_lemn',
  'relation': 'related_to',
  'label_ro': 'poate fi fixată pe șipci de lemn ale acoperișului',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_tigla',
  'dst': 'n_v4sti_metal',
  'relation': 'related_to',
  'label_ro': 'poate fi fixată cu accesorii metalice',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_caramida',
  'dst': 'n_v24_home_structure_perete',
  'relation': 'part_of',
  'label_ro': 'poate intra în alcătuirea unui perete',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 0},
 {'src': 'n_v1_19_caramida',
  'dst': 'n_v4soc_casa',
  'relation': 'related_to',
  'label_ro': 'poate fi folosită la construirea unei case',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_caramida',
  'dst': 'n_v32_garden_transport_roaba',
  'relation': 'related_to',
  'label_ro': 'poate fi transportată cu roaba',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_caramida',
  'dst': 'n_v4art_ceramica',
  'relation': 'related_to',
  'label_ro': 'cărămida arsă este un produs ceramic',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_mortar',
  'dst': 'n_v1_19_ciment',
  'relation': 'related_to',
  'label_ro': 'poate conține ciment drept liant',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_mortar',
  'dst': 'n_v4geo_nisip',
  'relation': 'related_to',
  'label_ro': 'poate conține nisip',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_mortar',
  'dst': 'n_v4gas_apa',
  'relation': 'related_to',
  'label_ro': 'poate fi preparat cu apă potabilă',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_mortar',
  'dst': 'n_v24_home_structure_perete',
  'relation': 'related_to',
  'label_ro': 'poate lega elementele unui perete',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_beton',
  'dst': 'n_v1_19_ciment',
  'relation': 'related_to',
  'label_ro': 'betonul de ciment folosește ciment ca liant',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_ciment',
  'dst': 'n_v28_nature_material_piatra',
  'relation': 'related_to',
  'label_ro': 'materiile sale prime pot include rocă de calcar',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_ciment',
  'dst': 'n_v24_home_structure_perete',
  'relation': 'related_to',
  'label_ro': 'intră în betoane folosite la pereți',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_beton',
  'dst': 'n_v4geo_nisip',
  'relation': 'related_to',
  'label_ro': 'poate conține nisip ca agregat fin',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_beton',
  'dst': 'n_v28_nature_material_piatra',
  'relation': 'related_to',
  'label_ro': 'poate conține piatră ca agregat grosier',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_beton',
  'dst': 'n_v24_home_structure_perete',
  'relation': 'related_to',
  'label_ro': 'poate forma pereți',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_beton',
  'dst': 'n_v32_garden_transport_roaba',
  'relation': 'related_to',
  'label_ro': 'betonul proaspăt poate fi transportat cu roaba',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_tencuiala',
  'dst': 'n_v1_19_beton',
  'relation': 'related_to',
  'label_ro': 'poate acoperi suprafețe din beton',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_tencuiala',
  'dst': 'n_v1_19_var',
  'relation': 'related_to',
  'label_ro': 'unele tencuieli folosesc var',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_tencuiala',
  'dst': 'n_v24_home_structure_perete',
  'relation': 'part_of',
  'label_ro': 'poate forma un strat pe perete',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 0},
 {'src': 'n_v1_19_tencuiala',
  'dst': 'n_v4art_vopsea',
  'relation': 'related_to',
  'label_ro': 'suprafața tencuită poate primi un strat de vopsea',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_var',
  'dst': 'n_v24_home_structure_perete',
  'relation': 'related_to',
  'label_ro': 'poate fi folosit la albirea pereților',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_var',
  'dst': 'n_v28_nature_material_piatra',
  'relation': 'related_to',
  'label_ro': 'se poate obține prin arderea pietrei de calcar',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_var',
  'dst': 'n_v4gas_apa',
  'relation': 'related_to',
  'label_ro': 'varul nestins reacționează cu apa',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_scandura',
  'dst': 'n_v1_3_material_lemn',
  'relation': 'related_to',
  'label_ro': 'este o piesă din lemn',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_scandura',
  'dst': 'n_v32_workshop_cut_fierastrau',
  'relation': 'related_to',
  'label_ro': 'poate fi tăiată cu fierăstrăul',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_scandura',
  'dst': 'n_v32_workshop_fastener_cui',
  'relation': 'related_to',
  'label_ro': 'poate fi prinsă cu un cui',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_scandura',
  'dst': 'n_v24_home_surfaces_podea',
  'relation': 'part_of',
  'label_ro': 'poate intra în alcătuirea podelei',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 0},
 {'src': 'n_v1_19_placaj',
  'dst': 'n_v1_3_material_lemn',
  'relation': 'related_to',
  'label_ro': 'este alcătuit din straturi subțiri de lemn',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_placaj',
  'dst': 'n_v24_home_storage_dulap',
  'relation': 'related_to',
  'label_ro': 'poate fi folosit la realizarea dulapurilor',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_placaj',
  'dst': 'n_v24_home_seating_scaun',
  'relation': 'related_to',
  'label_ro': 'poate fi folosit la realizarea scaunelor',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_placaj',
  'dst': 'n_v32_workshop_cut_fierastrau',
  'relation': 'related_to',
  'label_ro': 'poate fi tăiat cu fierăstrăul',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_sipca',
  'dst': 'n_v1_19_scandura',
  'relation': 'is_a',
  'label_ro': 'este o scândură îngustă',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 0},
 {'src': 'n_v1_19_sipca',
  'dst': 'n_v1_3_material_lemn',
  'relation': 'related_to',
  'label_ro': 'este făcută din lemn',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_sipca',
  'dst': 'n_v32_workshop_fastener_cui',
  'relation': 'related_to',
  'label_ro': 'poate fi prinsă cu un cui',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_sipca',
  'dst': 'n_v24_home_structure_acoperis',
  'relation': 'related_to',
  'label_ro': 'poate susține învelitoarea acoperișului',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_degetar',
  'dst': 'n_v24_body_limbs_deget',
  'relation': 'related_to',
  'label_ro': 'se poartă pe un deget la cusut',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_degetar',
  'dst': 'n_v4sti_metal',
  'relation': 'related_to',
  'label_ro': 'poate fi făcut din metal',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_degetar',
  'dst': 'n_v1_11_ata',
  'relation': 'related_to',
  'label_ro': 'protejează degetul la coaserea cu ață',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_degetar',
  'dst': 'n_v29_clothing_everyday_haina',
  'relation': 'related_to',
  'label_ro': 'poate fi folosit la cusutul hainelor',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_croseta',
  'dst': 'n_v1_11_lana',
  'relation': 'related_to',
  'label_ro': 'poate lucra fire din lână',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_croseta',
  'dst': 'n_v1_11_ata',
  'relation': 'related_to',
  'label_ro': 'lucrează un fir de ață cu ajutorul cârligului',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_croseta',
  'dst': 'n_v4sti_metal',
  'relation': 'related_to',
  'label_ro': 'poate fi fabricată din metal',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_croseta',
  'dst': 'n_v1_11_bumbac',
  'relation': 'related_to',
  'label_ro': 'poate lucra fire din bumbac',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_ghem',
  'dst': 'n_v1_11_lana',
  'relation': 'related_to',
  'label_ro': 'poate conține fir de lână înfășurat',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_ghem',
  'dst': 'n_v1_11_ata',
  'relation': 'related_to',
  'label_ro': 'poate fi format din ață înfășurată',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_ghem',
  'dst': 'n_v1_11_bumbac',
  'relation': 'related_to',
  'label_ro': 'poate conține fir din bumbac',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_ghem',
  'dst': 'n_v1_19_croseta',
  'relation': 'related_to',
  'label_ro': 'firul din ghem poate fi lucrat cu o croșetă',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_croitor',
  'dst': 'n_v28_work_occupation_meserie',
  'relation': 'related_to',
  'label_ro': 'practică meseria de a croi și coase haine',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_croitor',
  'dst': 'n_v4soc_munca',
  'relation': 'related_to',
  'label_ro': 'munca sa include croirea și coaserea hainelor',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_croitor',
  'dst': 'n_v29_clothing_everyday_haina',
  'relation': 'related_to',
  'label_ro': 'confecționează sau repară haine',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_croitor',
  'dst': 'n_v1_11_foarfeca',
  'relation': 'related_to',
  'label_ro': 'poate tăia materialul cu foarfeca',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_tamplar',
  'dst': 'n_v28_work_occupation_meserie',
  'relation': 'related_to',
  'label_ro': 'practică meseria de prelucrare a lemnului',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_tamplar',
  'dst': 'n_v4soc_munca',
  'relation': 'related_to',
  'label_ro': 'munca sa include prelucrarea lemnului',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_tamplar',
  'dst': 'n_v1_3_material_lemn',
  'relation': 'related_to',
  'label_ro': 'prelucrează lemnul',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_tamplar',
  'dst': 'n_v1_19_rindea',
  'relation': 'related_to',
  'label_ro': 'poate netezi lemnul cu rindeaua',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_fierar',
  'dst': 'n_v28_work_occupation_meserie',
  'relation': 'related_to',
  'label_ro': 'practică meseria de prelucrare a metalului',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_fierar',
  'dst': 'n_v4soc_munca',
  'relation': 'related_to',
  'label_ro': 'munca sa include prelucrarea metalului',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_fierar',
  'dst': 'n_v4sti_metal',
  'relation': 'related_to',
  'label_ro': 'prelucrează piese din metal',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_zidar',
  'dst': 'n_v28_work_occupation_meserie',
  'relation': 'related_to',
  'label_ro': 'practică meseria de a construi zidărie',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_zidar',
  'dst': 'n_v4soc_munca',
  'relation': 'related_to',
  'label_ro': 'munca sa include realizarea zidăriei',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_zidar',
  'dst': 'n_v24_home_structure_perete',
  'relation': 'related_to',
  'label_ro': 'construiește pereți din elemente de zidărie',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_zidar',
  'dst': 'n_v1_19_mistrie',
  'relation': 'related_to',
  'label_ro': 'poate întinde mortarul cu mistria',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_instalator',
  'dst': 'n_v28_work_occupation_meserie',
  'relation': 'related_to',
  'label_ro': 'practică o meserie de montare și întreținere a instalațiilor',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_instalator',
  'dst': 'n_v4soc_munca',
  'relation': 'related_to',
  'label_ro': 'munca sa include montarea sau repararea instalațiilor',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_instalator',
  'dst': 'n_v33_bathroom_fixture_robinet',
  'relation': 'related_to',
  'label_ro': 'poate monta sau repara robinete',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_instalator',
  'dst': 'n_v1_19_teava',
  'relation': 'related_to',
  'label_ro': 'poate monta sau repara țevi',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_electrician',
  'dst': 'n_v28_work_occupation_meserie',
  'relation': 'related_to',
  'label_ro': 'practică o meserie din domeniul instalațiilor electrice',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_electrician',
  'dst': 'n_v4soc_munca',
  'relation': 'related_to',
  'label_ro': 'munca sa include instalațiile electrice',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_electrician',
  'dst': 'n_v3sti_electricitate',
  'relation': 'related_to',
  'label_ro': 'lucrează cu instalații care folosesc electricitate',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_electrician',
  'dst': 'n_v33_electric_outlet_priza',
  'relation': 'related_to',
  'label_ro': 'poate monta sau repara prize electrice',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_atelier',
  'dst': 'n_v4soc_munca',
  'relation': 'related_to',
  'label_ro': 'este un spațiu în care se desfășoară muncă',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_atelier',
  'dst': 'n_v4soc_fabrica',
  'relation': 'part_of',
  'label_ro': 'poate fi o secție a unei fabrici',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 0},
 {'src': 'n_v1_19_atelier',
  'dst': 'n_v32_workshop_hand_ciocan',
  'relation': 'related_to',
  'label_ro': 'un atelier de prelucrare poate folosi ciocane',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_atelier',
  'dst': 'n_v1_19_masina_de_cusut',
  'relation': 'related_to',
  'label_ro': 'un atelier de croitorie poate folosi mașini de cusut',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_trusa',
  'dst': 'n_v1_11_cutie',
  'relation': 'related_to',
  'label_ro': 'poate păstra uneltele într-o cutie',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_trusa',
  'dst': 'n_v32_workshop_hand_ciocan',
  'relation': 'related_to',
  'label_ro': 'o trusă de unelte poate include un ciocan',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_trusa',
  'dst': 'n_v32_workshop_hand_surubelnita',
  'relation': 'related_to',
  'label_ro': 'o trusă de unelte poate include o șurubelniță',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_trusa',
  'dst': 'n_v32_workshop_hand_cleste',
  'relation': 'related_to',
  'label_ro': 'o trusă de unelte poate include un clește',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v32_workshop_hand_ciocan',
  'dst': 'n_v1_19_unealta',
  'relation': 'is_a',
  'label_ro': 'este o unealtă',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 0},
 {'src': 'n_v32_workshop_hand_cleste',
  'dst': 'n_v1_19_unealta',
  'relation': 'is_a',
  'label_ro': 'este o unealtă',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 0},
 {'src': 'n_v32_workshop_cut_fierastrau',
  'dst': 'n_v1_19_unealta',
  'relation': 'is_a',
  'label_ro': 'este o unealtă',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 0},
 {'src': 'n_v32_workshop_hand_surubelnita',
  'dst': 'n_v1_19_unealta',
  'relation': 'is_a',
  'label_ro': 'este o unealtă',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 0},
 {'src': 'n_v1_12_sapa',
  'dst': 'n_v1_19_unealta',
  'relation': 'is_a',
  'label_ro': 'este o unealtă',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 0},
 {'src': 'n_v1_19_masina_de_cusut',
  'dst': 'n_v1_11_ata',
  'relation': 'related_to',
  'label_ro': 'formează cusături cu ață',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_masina_de_cusut',
  'dst': 'n_v29_clothing_everyday_haina',
  'relation': 'related_to',
  'label_ro': 'poate fi folosită la confecționarea hainelor',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_masina_de_cusut',
  'dst': 'n_v1_11_panza',
  'relation': 'related_to',
  'label_ro': 'poate coase bucăți de pânză',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_masina_de_cusut',
  'dst': 'n_v3sti_electricitate',
  'relation': 'related_to',
  'label_ro': 'modelele electrice folosesc electricitate',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_andrele',
  'dst': 'n_v1_11_lana',
  'relation': 'related_to',
  'label_ro': 'pot lucra fire din lână',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_andrele',
  'dst': 'n_v1_11_ata',
  'relation': 'related_to',
  'label_ro': 'pot forma ochiuri din ață',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_andrele',
  'dst': 'n_v1_11_bumbac',
  'relation': 'related_to',
  'label_ro': 'pot lucra fire din bumbac',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_andrele',
  'dst': 'n_v4sti_metal',
  'relation': 'related_to',
  'label_ro': 'pot fi fabricate din metal',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_panglica',
  'dst': 'n_v29_clothing_everyday_haina',
  'relation': 'related_to',
  'label_ro': 'poate decora o haină',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_panglica',
  'dst': 'n_v30_clothing_everyday_rochie',
  'relation': 'related_to',
  'label_ro': 'poate decora o rochie',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_panglica',
  'dst': 'n_v1_9_palarie',
  'relation': 'related_to',
  'label_ro': 'poate decora o pălărie',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_panglica',
  'dst': 'n_v1_11_panza',
  'relation': 'related_to',
  'label_ro': 'poate fi realizată ca o fâșie de pânză',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_petic',
  'dst': 'n_v1_11_panza',
  'relation': 'related_to',
  'label_ro': 'poate fi o bucată de pânză',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_petic',
  'dst': 'n_v29_clothing_everyday_haina',
  'relation': 'related_to',
  'label_ro': 'poate repara o parte ruptă din haină',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_petic',
  'dst': 'n_v30_clothing_everyday_pantaloni',
  'relation': 'related_to',
  'label_ro': 'poate întări o parte a pantalonilor',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_petic',
  'dst': 'n_v1_11_ata',
  'relation': 'related_to',
  'label_ro': 'poate fi prins prin coasere cu ață',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_cusatura',
  'dst': 'n_v1_11_ata',
  'relation': 'related_to',
  'label_ro': 'se poate realiza cu ață',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_cusatura',
  'dst': 'n_v1_11_panza',
  'relation': 'related_to',
  'label_ro': 'poate uni bucăți de pânză',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_cusatura',
  'dst': 'n_v29_clothing_everyday_haina',
  'relation': 'part_of',
  'label_ro': 'poate uni părți ale unei haine',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 0},
 {'src': 'n_v1_19_cusatura',
  'dst': 'n_v1_19_masina_de_cusut',
  'relation': 'related_to',
  'label_ro': 'se poate realiza cu mașina de cusut',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_tiv',
  'dst': 'n_v1_19_cusatura',
  'relation': 'related_to',
  'label_ro': 'poate fi fixat prin cusătură',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_tiv',
  'dst': 'n_v30_clothing_everyday_rochie',
  'relation': 'part_of',
  'label_ro': 'poate finisa marginea unei rochii',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 0},
 {'src': 'n_v1_19_tiv',
  'dst': 'n_v30_clothing_everyday_pantaloni',
  'relation': 'part_of',
  'label_ro': 'poate finisa marginea pantalonilor',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 0},
 {'src': 'n_v1_19_tiv',
  'dst': 'n_v1_11_ata',
  'relation': 'related_to',
  'label_ro': 'poate fi fixat prin coasere cu ață',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_broderie',
  'dst': 'n_v1_11_ata',
  'relation': 'related_to',
  'label_ro': 'poate fi realizată cu ață pentru modele decorative',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_broderie',
  'dst': 'n_v1_11_panza',
  'relation': 'related_to',
  'label_ro': 'poate decora pânza',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_broderie',
  'dst': 'n_v29_clothing_everyday_haina',
  'relation': 'related_to',
  'label_ro': 'poate decora o haină',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1},
 {'src': 'n_v1_19_broderie',
  'dst': 'n_v30_clothing_everyday_rochie',
  'relation': 'related_to',
  'label_ro': 'poate decora o rochie',
  'strength': 0.75,
  'is_distractor': 0,
  'bidirectional': 1})

ALIASES = {'n_v32_workshop_hand_ciocan': ['ciocanelor'],
 'n_v32_workshop_fastener_surub': ['șuruburilor'],
 'n_v32_workshop_cut_fierastrau': ['fierăstraielor'],
 'n_v32_workshop_hand_cleste': ['cleștilor'],
 'n_v32_workshop_hand_surubelnita': ['șurubelnițelor']}

REGIONAL_INPUTS = {}

ITEM_EVIDENCE = ({'id': 'v119-diblu',
  'lemma': 'Diblu',
  'kind': 'new_shared_concept',
  'node_id': 'n_v1_19_diblu',
  'games': ['Cald sau Rece', 'Lanțul Cuvintelor', 'Conexiuni', 'Intrusul'],
  'sense': 'Piesă din lemn,plastic sau metal introdusă în zidărie pentru fixarea unui cui sau '
           'șurub.',
  'register': 'Selected everyday workshop/craft noun sense; unrelated,archaic/poetic-only meanings '
              'excluded;no instructions or clinical ruling.',
  'verified_forms': ['diblu', 'diblul', 'dibluri', 'diblurile', 'diblului', 'diblurilor'],
  'proposed_forms': ['diblu', 'diblul', 'dibluri', 'diblurile', 'diblului', 'diblurilor'],
  'already_resolved_forms': [],
  'already_reserved_forms': [],
  'excluded_form_hypotheses': [],
  'dictionaries': [{'lemma': 'diblu',
                    'url': 'https://dexonline.ro/definitie/diblu/json',
                    'dex_definition_ids': ['860295'],
                    'doom3_definition_ids': ['1307673'],
                    'flexion_url': 'https://dexonline.ro/definitie/diblu',
                    'flexion_authority': 'Explicit DOOM3 neuter diblu table;ordinary unelided rows '
                                         'only',
                    'forms_note': 'diblu/diblul/dibluri/diblurile/diblului/diblurilor;exclude '
                                  'elided diblu- and vocatives.',
                    'paraphrase': 'Piesă din lemn,plastic sau metal introdusă în zidărie pentru '
                                  'fixarea unui cui sau șurub.; selected DEX sense/register and '
                                  'DOOM3 lexical gender/number checked, ordinary forms from '
                                  'Explicit DOOM3 neuter diblu table;ordinary unelided rows '
                                  'only.'}],
  'sources': [{'url': 'https://dexonline.ro/definitie/diblu/json',
               'paraphrase': 'Piesă din lemn,plastic sau metal introdusă în zidărie pentru fixarea '
                             'unui cui sau șurub.; selected DEX sense/register and DOOM3 lexical '
                             'gender/number checked, ordinary forms from Explicit DOOM3 neuter '
                             'diblu table;ordinary unelided rows only.'},
              {'url': 'https://ro.wiktionary.org/wiki/diblu',
               'paraphrase': 'Confirmă piesa de lemn sau metal introdusă în zid și paradigma '
                             'neutră obișnuită.'}],
  'link_targets': [{'node_id': 'n_v32_workshop_fastener_surub',
                    'label': 'Șurub',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'poate fixa un șurub într-o gaură',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_diblu',
                    'edge_dst': 'n_v32_workshop_fastener_surub',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://dexonline.ro/definitie/diblu/json'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v24_home_structure_perete',
                    'label': 'Perete',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'poate fi introdus într-o gaură din perete',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_diblu',
                    'edge_dst': 'n_v24_home_structure_perete',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://dexonline.ro/definitie/diblu/json',
                                'https://ro.wiktionary.org/wiki/diblu'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v1_3_material_lemn',
                    'label': 'Lemn',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'poate fi o piesă din lemn',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_diblu',
                    'edge_dst': 'n_v1_3_material_lemn',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://dexonline.ro/definitie/diblu/json',
                                'https://ro.wiktionary.org/wiki/diblu'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v4sti_metal',
                    'label': 'metal',
                    'category': 'stiinta',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'există dibluri metalice pentru fixare',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_diblu',
                    'edge_dst': 'n_v4sti_metal',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://dexonline.ro/definitie/diblu/json',
                                'https://ro.wiktionary.org/wiki/diblu'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'}],
  'current_graph_counts': {'distinct': 4, 'old_main': 4, 'same_category': 3, 'batch': 0},
  'frequency': {'url': 'https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/ro/ro_50k.txt',
                'best_rank': None,
                'matched_form': None,
                'role': 'Positive signal only; absence does not reject concrete everyday/school '
                        'vocabulary.'},
  'scope': 'Accepted after both once-only independent whole-batch web reviews and explicit verdict '
           'application;reviewed/unapplied/not_landed. No game round,target,recipe,route or '
           'runtime qualification.',
  'review_verdicts': {'factual': {'verdict': 'accept',
                                  'rationale': 'Piesa de fixare din zidărie este sensul curent; '
                                               'paradigma neutră și toate cele șase chei sunt '
                                               'confirmate.'},
                      'quality': {'verdict': 'accept',
                                  'rationale': 'Concrete household fixing noun: a current Romanian '
                                               'manufacturer explains the wall-plug and screw use; '
                                               'the definition and complete neuter family '
                                               'agree.'}}},
 {'id': 'v119-pila',
  'lemma': 'Pilă',
  'kind': 'new_shared_concept',
  'node_id': 'n_v1_19_pila',
  'games': ['Cald sau Rece', 'Lanțul Cuvintelor', 'Conexiuni', 'Intrusul'],
  'sense': 'Unealtă așchietoare cu dinți mici pe suprafață pentru ajustarea pieselor;excluse pila '
           'electrică,reactorul și protecția prin relații.',
  'register': 'Selected everyday workshop/craft noun sense; unrelated,archaic/poetic-only meanings '
              'excluded;no instructions or clinical ruling.',
  'verified_forms': ['pilă', 'pile', 'pilele', 'pilei', 'pilelor'],
  'proposed_forms': ['pilă', 'pile', 'pilele', 'pilei', 'pilelor'],
  'already_resolved_forms': [],
  'already_reserved_forms': [],
  'excluded_form_hypotheses': [],
  'dictionaries': [{'lemma': 'pilă',
                    'url': 'https://dexonline.ro/definitie/pil%C4%83/json',
                    'dex_definition_ids': ['871503'],
                    'doom3_definition_ids': ['1282491'],
                    'flexion_url': 'https://dexonline.ro/definitie/pil%C4%83',
                    'flexion_authority': 'DOOM3 feminine pilă plus second explicit DOR F1 table '
                                         'labeled pilă (unealtă)',
                    'forms_note': 'pilă/pila/pile/pilele/pilei/pilelor;not '
                                  'electrical/bridge/figurative noun senses;no vocatives.',
                    'paraphrase': 'Unealtă așchietoare cu dinți mici pe suprafață pentru ajustarea '
                                  'pieselor;excluse pila electrică,reactorul și protecția prin '
                                  'relații.; selected DEX sense/register and DOOM3 lexical '
                                  'gender/number checked, ordinary forms from DOOM3 feminine pilă '
                                  'plus second explicit DOR F1 table labeled pilă (unealtă).'}],
  'sources': [{'url': 'https://dexonline.ro/definitie/pil%C4%83/json',
               'paraphrase': 'Unealtă așchietoare cu dinți mici pe suprafață pentru ajustarea '
                             'pieselor;excluse pila electrică,reactorul și protecția prin '
                             'relații.; selected DEX sense/register and DOOM3 lexical '
                             'gender/number checked, ordinary forms from DOOM3 feminine pilă plus '
                             'second explicit DOR F1 table labeled pilă (unealtă).'},
              {'url': 'https://ro.wiktionary.org/wiki/pil%C4%83',
               'paraphrase': 'Secțiunea de unealtă confirmă oțelul călit și paradigma feminină;nu '
                             'se preia etimologia de la omonimul electric.'},
              {'url': 'https://spitalpneumoftiziologieaiud.ro/wp-content/uploads/2019/11/Caiet-de-instruire-practica-Domeniul-mecanica-notiuni-de-lacatuserie-generala.pdf',
               'paraphrase': 'Lecția11 prezintă corpul pilei din oțel,mânerul din lemn și lucrul '
                             'la menghină.'},
              {'url': 'https://mec.gov.md/sites/default/files/10_educatie_tehnologica_manual_pentru_clasa_a_vi-a_lotul_10_reevaluare_compressed.pdf',
               'paraphrase': 'Pasajul indexat din manualul primar de educație '
                             'tehnologică,p79,arată ascuțirea dinților fierăstrăului de tâmplărie '
                             'cu pila;cererea directă a expirat,nu se pretinde citirea PDF '
                             'integral.'},
              {'url': 'https://www.autocv.ro/wp-content/uploads/2020/03/pilirea-metalelor-clasa-a-9-a-M2.pdf',
               'paraphrase': 'Pasajul indexat al lecției pentru clasaIX explică fixarea piesei '
                             'pilite în menghină.'}],
  'link_targets': [{'node_id': 'n_v4sti_metal',
                    'label': 'metal',
                    'category': 'stiinta',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'unealta poate fi confecționată din oțel',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_pila',
                    'edge_dst': 'n_v4sti_metal',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://ro.wiktionary.org/wiki/pil%C4%83',
                                'https://spitalpneumoftiziologieaiud.ro/wp-content/uploads/2019/11/Caiet-de-instruire-practica-Domeniul-mecanica-notiuni-de-lacatuserie-generala.pdf'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v1_3_material_lemn',
                    'label': 'Lemn',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'mânerul său poate fi din lemn',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_pila',
                    'edge_dst': 'n_v1_3_material_lemn',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://spitalpneumoftiziologieaiud.ro/wp-content/uploads/2019/11/Caiet-de-instruire-practica-Domeniul-mecanica-notiuni-de-lacatuserie-generala.pdf'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v32_workshop_cut_fierastrau',
                    'label': 'Fierăstrău',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'o pilă de ascuțit poate prelucra dinții fierăstrăului',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_pila',
                    'edge_dst': 'n_v32_workshop_cut_fierastrau',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://mec.gov.md/sites/default/files/10_educatie_tehnologica_manual_pentru_clasa_a_vi-a_lotul_10_reevaluare_compressed.pdf'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v1_19_menghina',
                    'label': 'Menghină',
                    'category': 'viata_de_roman',
                    'status': 'batch',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'piesa pilită poate fi fixată într-o menghină',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_pila',
                    'edge_dst': 'n_v1_19_menghina',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://www.autocv.ro/wp-content/uploads/2020/03/pilirea-metalelor-clasa-a-9-a-M2.pdf',
                                'https://spitalpneumoftiziologieaiud.ro/wp-content/uploads/2019/11/Caiet-de-instruire-practica-Domeniul-mecanica-notiuni-de-lacatuserie-generala.pdf'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'}],
  'source_acquisition_note': 'School manual and AUTOCV passages read through indexed web-reader '
                             'excerpts;primary caiet direct status is in request trace. No '
                             'technical instructions are adopted.',
  'current_graph_counts': {'distinct': 4, 'old_main': 3, 'same_category': 3, 'batch': 1},
  'frequency': {'url': 'https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/ro/ro_50k.txt',
                'best_rank': 38236,
                'matched_form': 'pile',
                'role': 'Positive signal only; absence does not reject concrete everyday/school '
                        'vocabulary.'},
  'scope': 'Accepted after both once-only independent whole-batch web reviews and explicit verdict '
           'application;reviewed/unapplied/not_landed. No game round,target,recipe,route or '
           'runtime qualification.',
  'review_verdicts': {'factual': {'verdict': 'accept',
                                  'rationale': 'Este selectată unealta de ajustare, cu flexiune '
                                               'feminină DOR F1 compatibilă cu DOOM3; omonimele '
                                               'electrice și figurate rămân excluse.'},
                      'quality': {'verdict': 'accept',
                                  'rationale': 'An ordinary workshop file taught in Romanian '
                                               'technical lessons; the tool sense is clear, while '
                                               'electrical and figurative senses add no inputs.'}}},
 {'id': 'v119-rindea',
  'lemma': 'Rindea',
  'kind': 'new_shared_concept',
  'node_id': 'n_v1_19_rindea',
  'games': ['Cald sau Rece', 'Lanțul Cuvintelor', 'Conexiuni', 'Intrusul', 'Perechi'],
  'sense': 'Unealtă pentru netezirea și fasonarea lemnului prin așchiere;excluse sensul de '
           'prelucrare a metalelor moi și variantele regionale nescreenate.',
  'register': 'Selected everyday workshop/craft noun sense; unrelated,archaic/poetic-only meanings '
              'excluded;no instructions or clinical ruling.',
  'verified_forms': ['rindea', 'rindeaua', 'rindele', 'rindelele', 'rindelei', 'rindelelor'],
  'proposed_forms': ['rindea', 'rindeaua', 'rindele', 'rindelele', 'rindelei', 'rindelelor'],
  'already_resolved_forms': [],
  'already_reserved_forms': [],
  'excluded_form_hypotheses': [{'form': 'rindelii',
                                'reason': 'Not the selected DOOM3 rindelei genitive;hypothesis '
                                          'excluded.'}],
  'dictionaries': [{'lemma': 'rindea',
                    'url': 'https://dexonline.ro/definitie/rindea/json',
                    'dex_definition_ids': ['858657'],
                    'doom3_definition_ids': ['1300554'],
                    'flexion_url': 'https://dexonline.ro/definitie/rindea',
                    'flexion_authority': 'DOOM3 rindeaua/rindelei/rindele plus first DOR table for '
                                         'rindea,not regional rândea table',
                    'forms_note': 'rindea/rindeaua/rindele/rindelele/rindelei/rindelelor;exclude '
                                  'rindelii and unscreened regional variants.',
                    'paraphrase': 'Unealtă pentru netezirea și fasonarea lemnului prin '
                                  'așchiere;excluse sensul de prelucrare a metalelor moi și '
                                  'variantele regionale nescreenate.; selected DEX sense/register '
                                  'and DOOM3 lexical gender/number checked, ordinary forms from '
                                  'DOOM3 rindeaua/rindelei/rindele plus first DOR table for '
                                  'rindea,not regional rândea table.'}],
  'sources': [{'url': 'https://dexonline.ro/definitie/rindea/json',
               'paraphrase': 'Unealtă pentru netezirea și fasonarea lemnului prin așchiere;excluse '
                             'sensul de prelucrare a metalelor moi și variantele regionale '
                             'nescreenate.; selected DEX sense/register and DOOM3 lexical '
                             'gender/number checked, ordinary forms from DOOM3 '
                             'rindeaua/rindelei/rindele plus first DOR table for rindea,not '
                             'regional rândea table.'},
              {'url': 'https://ro.wiktionary.org/wiki/rindea',
               'paraphrase': 'Confirmă sensul de prelucrare a lemnului și paradigma '
                             'rindeaua/rindelei/rindele.'},
              {'url': 'https://mec.gov.md/sites/default/files/17_manual_compressed.pdf',
               'paraphrase': 'Manualul primar de educație tehnologică prezintă corpuri din lemn '
                             'sau metal și rindeluirea suprafeței unei scânduri pe masa '
                             'tâmplarului.'}],
  'link_targets': [{'node_id': 'n_v1_3_material_lemn',
                    'label': 'Lemn',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'netezește suprafețe din lemn',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_rindea',
                    'edge_dst': 'n_v1_3_material_lemn',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://dexonline.ro/definitie/rindea/json',
                                'https://ro.wiktionary.org/wiki/rindea',
                                'https://mec.gov.md/sites/default/files/17_manual_compressed.pdf'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v1_19_scandura',
                    'label': 'Scândură',
                    'category': 'viata_de_roman',
                    'status': 'batch',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'poate netezi suprafața unei scânduri',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_rindea',
                    'edge_dst': 'n_v1_19_scandura',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://mec.gov.md/sites/default/files/17_manual_compressed.pdf'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v4sti_metal',
                    'label': 'metal',
                    'category': 'stiinta',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'unele modele au corp din metal',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_rindea',
                    'edge_dst': 'n_v4sti_metal',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://mec.gov.md/sites/default/files/17_manual_compressed.pdf'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'}],
  'source_acquisition_note': 'Primary manual passage read via indexed web reader;direct '
                             'acquisition status retained in trace.',
  'current_graph_counts': {'distinct': 4, 'old_main': 2, 'same_category': 2, 'batch': 2},
  'frequency': {'url': 'https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/ro/ro_50k.txt',
                'best_rank': None,
                'matched_form': None,
                'role': 'Positive signal only; absence does not reject concrete everyday/school '
                        'vocabulary.'},
  'scope': 'Accepted after both once-only independent whole-batch web reviews and explicit verdict '
           'application;reviewed/unapplied/not_landed. No game round,target,recipe,route or '
           'runtime qualification.',
  'review_verdicts': {'factual': {'verdict': 'accept',
                                  'rationale': 'Sensul de netezire a lemnului și familia '
                                               'rindeaua/rindelei sunt confirmate; forma rindelii '
                                               'și varianta regională nu sunt admise.'},
                      'quality': {'verdict': 'accept',
                                  'rationale': 'A named woodworking tool in Romanian-language '
                                               'school lessons and current carpentry catalogues; '
                                               'normative rindelei is retained.'}}},
 {'id': 'v119-dalta',
  'lemma': 'Daltă',
  'kind': 'new_shared_concept',
  'node_id': 'n_v1_19_dalta',
  'games': ['Cald sau Rece', 'Lanțul Cuvintelor', 'Conexiuni', 'Intrusul'],
  'sense': 'Unealtă de oțel cu tăiș în formă de pană pentru crestat,cioplit,scobit sau tăiat '
           'materiale.',
  'register': 'Selected everyday workshop/craft noun sense; unrelated,archaic/poetic-only meanings '
              'excluded;no instructions or clinical ruling.',
  'verified_forms': ['daltă', 'dălți', 'dălțile', 'dălții', 'dălților'],
  'proposed_forms': ['daltă', 'dălți', 'dălțile', 'dălții', 'dălților'],
  'already_resolved_forms': [],
  'already_reserved_forms': [],
  'excluded_form_hypotheses': [{'form': 'dalte',
                                'reason': 'Not the selected DOOM3 dălți/dălții paradigm;unverified '
                                          'alternate hypothesis excluded.'},
                               {'form': 'daltele',
                                'reason': 'Not the selected DOOM3 dălți/dălții paradigm;unverified '
                                          'alternate hypothesis excluded.'},
                               {'form': 'daltei',
                                'reason': 'Not the selected DOOM3 dălți/dălții paradigm;unverified '
                                          'alternate hypothesis excluded.'},
                               {'form': 'daltelor',
                                'reason': 'Not the selected DOOM3 dălți/dălții paradigm;unverified '
                                          'alternate hypothesis excluded.'}],
  'dictionaries': [{'lemma': 'daltă',
                    'url': 'https://dexonline.ro/definitie/dalt%C4%83/json',
                    'dex_definition_ids': ['855515'],
                    'doom3_definition_ids': ['1305422'],
                    'flexion_url': 'https://dexonline.ro/definitie/dalt%C4%83',
                    'flexion_authority': 'DOOM3 feminine dălții/dălți entry plus matching DOR noun '
                                         'table',
                    'forms_note': 'daltă/dalta/dălți/dălțile/dălții/dălților;fold-equivalent dalta '
                                  'omitted;exclude alternate -e forms.',
                    'paraphrase': 'Unealtă de oțel cu tăiș în formă de pană pentru '
                                  'crestat,cioplit,scobit sau tăiat materiale.; selected DEX '
                                  'sense/register and DOOM3 lexical gender/number checked, '
                                  'ordinary forms from DOOM3 feminine dălții/dălți entry plus '
                                  'matching DOR noun table.'}],
  'sources': [{'url': 'https://dexonline.ro/definitie/dalt%C4%83/json',
               'paraphrase': 'Unealtă de oțel cu tăiș în formă de pană pentru '
                             'crestat,cioplit,scobit sau tăiat materiale.; selected DEX '
                             'sense/register and DOOM3 lexical gender/number checked, ordinary '
                             'forms from DOOM3 feminine dălții/dălți entry plus matching DOR noun '
                             'table.'},
              {'url': 'https://ro.wiktionary.org/wiki/dalt%C4%83',
               'paraphrase': 'Confirmă unealta de oțel și paradigma feminină cu pluralul dălți.'},
              {'url': 'https://ro.wikipedia.org/wiki/Dalt%C4%83',
               'paraphrase': 'Descrie unealta din oțel folosită în sculptură și tâmplărie și '
                             'ilustrează o daltă pentru lemn.'},
              {'url': 'https://spitalpneumoftiziologieaiud.ro/wp-content/uploads/2019/11/Caiet-de-instruire-practica-Domeniul-mecanica-notiuni-de-lacatuserie-generala.pdf',
               'paraphrase': 'Pasajul despre debitarea cu dalta,p44,din PDF citit în cache în '
                             'acest tick,confirmă lovirea dălții cu ciocanul.'},
              {'url': 'https://mec.gov.md/sites/default/files/10_educatie_tehnologica_manual_pentru_clasa_a_vi-a_lotul_10_reevaluare_compressed.pdf',
               'paraphrase': 'Pasajul primar indexat,p75,distinge dălțile lovite cu ciocanul de '
                             'dălțile de finisare;nu se generalizează folosirea ciocanului.'}],
  'link_targets': [{'node_id': 'n_v1_3_material_lemn',
                    'label': 'Lemn',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'o daltă de tâmplărie prelucrează lemnul',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_dalta',
                    'edge_dst': 'n_v1_3_material_lemn',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://ro.wikipedia.org/wiki/Dalt%C4%83',
                                'https://mec.gov.md/sites/default/files/10_educatie_tehnologica_manual_pentru_clasa_a_vi-a_lotul_10_reevaluare_compressed.pdf'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v4sti_metal',
                    'label': 'metal',
                    'category': 'stiinta',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'are o parte tăietoare din metal',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_dalta',
                    'edge_dst': 'n_v4sti_metal',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://dexonline.ro/definitie/dalt%C4%83/json',
                                'https://ro.wikipedia.org/wiki/Dalt%C4%83'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_sculptura',
                    'label': 'Sculptură',
                    'category': 'personalitati',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'poate fi folosită la realizarea sculpturii',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_dalta',
                    'edge_dst': 'n_sculptura',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://dexonline.ro/definitie/dalt%C4%83/json',
                                'https://ro.wikipedia.org/wiki/Dalt%C4%83',
                                'https://mec.gov.md/sites/default/files/10_educatie_tehnologica_manual_pentru_clasa_a_vi-a_lotul_10_reevaluare_compressed.pdf'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v32_workshop_hand_ciocan',
                    'label': 'Ciocan',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'unele dălți se folosesc prin lovire cu ciocanul',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_dalta',
                    'edge_dst': 'n_v32_workshop_hand_ciocan',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://spitalpneumoftiziologieaiud.ro/wp-content/uploads/2019/11/Caiet-de-instruire-practica-Domeniul-mecanica-notiuni-de-lacatuserie-generala.pdf',
                                'https://mec.gov.md/sites/default/files/10_educatie_tehnologica_manual_pentru_clasa_a_vi-a_lotul_10_reevaluare_compressed.pdf'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'}],
  'source_acquisition_note': 'Caiet direct PDF text reused from same-tick Pilă cache;MEC manual '
                             'passage read through indexed primary excerpt;no work instructions '
                             'adopted.',
  'current_graph_counts': {'distinct': 4, 'old_main': 4, 'same_category': 2, 'batch': 0},
  'frequency': {'url': 'https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/ro/ro_50k.txt',
                'best_rank': None,
                'matched_form': None,
                'role': 'Positive signal only; absence does not reject concrete everyday/school '
                        'vocabulary.'},
  'scope': 'Accepted after both once-only independent whole-batch web reviews and explicit verdict '
           'application;reviewed/unapplied/not_landed. No game round,target,recipe,route or '
           'runtime qualification.',
  'review_verdicts': {'factual': {'verdict': 'accept',
                                  'rationale': 'Unealta cu tăiș este confirmată, cu pluralul '
                                               'normativ dălți și genitivul dălții; familia '
                                               'alternativă -e rămâne exclusă.'},
                      'quality': {'verdict': 'accept',
                                  'rationale': 'School woodworking and practical metalwork '
                                               'establish the familiar chisel sense; dălți/dălții '
                                               'agree with current norm.'}}},
 {'id': 'v119-burghiu',
  'lemma': 'Burghiu',
  'kind': 'new_shared_concept',
  'node_id': 'n_v1_19_burghiu',
  'games': ['Cald sau Rece', 'Lanțul Cuvintelor', 'Conexiuni', 'Intrusul', 'Perechi'],
  'sense': 'Unealtă așchietoare de oțel pentru găurirea materialelor,distinctă de mașina care o '
           'antrenează.',
  'register': 'Selected everyday workshop/craft noun sense; unrelated,archaic/poetic-only meanings '
              'excluded;no instructions or clinical ruling.',
  'verified_forms': ['burghiu', 'burghiul', 'burghie', 'burghiele', 'burghiului', 'burghielor'],
  'proposed_forms': ['burghiu', 'burghiul', 'burghie', 'burghiele', 'burghiului', 'burghielor'],
  'already_resolved_forms': [],
  'already_reserved_forms': [],
  'excluded_form_hypotheses': [],
  'dictionaries': [{'lemma': 'burghiu',
                    'url': 'https://dexonline.ro/definitie/burghiu/json',
                    'dex_definition_ids': ['839130'],
                    'doom3_definition_ids': ['1320079'],
                    'flexion_url': 'https://dexonline.ro/definitie/burghiu',
                    'flexion_authority': 'First explicit DOOM3 neuter table for burghiu,not the '
                                         'feminine variant burghie table',
                    'forms_note': 'burghiu/burghiul/burghie/burghiele/burghiului/burghielor;no '
                                  'elided burghiu-,vocatives or feminine-variant forms.',
                    'paraphrase': 'Unealtă așchietoare de oțel pentru găurirea '
                                  'materialelor,distinctă de mașina care o antrenează.; selected '
                                  'DEX sense/register and DOOM3 lexical gender/number checked, '
                                  'ordinary forms from First explicit DOOM3 neuter table for '
                                  'burghiu,not the feminine variant burghie table.'}],
  'sources': [{'url': 'https://dexonline.ro/definitie/burghiu/json',
               'paraphrase': 'Unealtă așchietoare de oțel pentru găurirea materialelor,distinctă '
                             'de mașina care o antrenează.; selected DEX sense/register and DOOM3 '
                             'lexical gender/number checked, ordinary forms from First explicit '
                             'DOOM3 neuter table for burghiu,not the feminine variant burghie '
                             'table.'},
              {'url': 'https://ro.wiktionary.org/wiki/burghiu',
               'paraphrase': 'Confirmă unealta de oțel pentru găurire și paradigma neutră '
                             'burghiul/burghie.'},
              {'url': 'https://www.bosch-diy.com/ro/ro/catalog-online-accesorii-diy/g%C4%83urire',
               'paraphrase': 'Catalogul producătorului listează explicit burghie pentru lemn și '
                             'seturi pentru metal și zidărie.'},
              {'url': 'https://www.bosch-diy.com/ro/ro/p/burghiu-universal-2762959',
               'paraphrase': 'Pagina burghiului universal îl asociază explicit cu mașinile de '
                             'găurit;nu se preiau instrucțiuni sau recomandări de utilizare.'}],
  'link_targets': [{'node_id': 'n_v1_19_bormasina',
                    'label': 'Bormașină',
                    'category': 'viata_de_roman',
                    'status': 'batch',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'poate roti un burghiu',
                    'direction': 'incoming',
                    'edge_src': 'n_v1_19_bormasina',
                    'edge_dst': 'n_v1_19_burghiu',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://www.bosch-diy.com/ro/ro/p/burghiu-universal-2762959'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v4sti_metal',
                    'label': 'metal',
                    'category': 'stiinta',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'poate fi fabricat din metal',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_burghiu',
                    'edge_dst': 'n_v4sti_metal',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://dexonline.ro/definitie/burghiu/json',
                                'https://ro.wiktionary.org/wiki/burghiu'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v1_3_material_lemn',
                    'label': 'Lemn',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'un burghiu pentru lemn execută găuri în lemn',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_burghiu',
                    'edge_dst': 'n_v1_3_material_lemn',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://www.bosch-diy.com/ro/ro/catalog-online-accesorii-diy/g%C4%83urire'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v24_home_structure_perete',
                    'label': 'Perete',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'un burghiu pentru zidărie execută găuri în perete',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_burghiu',
                    'edge_dst': 'n_v24_home_structure_perete',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://www.bosch-diy.com/ro/ro/catalog-online-accesorii-diy/g%C4%83urire',
                                'https://www.bosch-diy.com/ro/ro/p/burghiu-universal-2762959'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'}],
  'source_quality_warnings': ['Numerical power/depth inconsistencies on the separately read '
                              'machine product page are not used;no numbers or machine '
                              'specification claims adopted.'],
  'current_graph_counts': {'distinct': 4, 'old_main': 3, 'same_category': 3, 'batch': 1},
  'frequency': {'url': 'https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/ro/ro_50k.txt',
                'best_rank': 35896,
                'matched_form': 'burghiu',
                'role': 'Positive signal only; absence does not reject concrete everyday/school '
                        'vocabulary.'},
  'scope': 'Accepted after both once-only independent whole-batch web reviews and explicit verdict '
           'application;reviewed/unapplied/not_landed. No game round,target,recipe,route or '
           'runtime qualification.',
  'review_verdicts': {'factual': {'verdict': 'accept',
                                  'rationale': 'Este unealta rotitoare de găurire, distinctă de '
                                               'mașină; tabelul neutru burghiu/burghie confirmă '
                                               'familia.'},
                      'quality': {'verdict': 'accept',
                                  'rationale': 'School and household drilling usage distinguish '
                                               'the bit from its machine; all six neuter keys are '
                                               'supported.'}}},
 {'id': 'v119-bormasina',
  'lemma': 'Bormașină',
  'kind': 'new_shared_concept',
  'node_id': 'n_v1_19_bormasina',
  'games': ['Cald sau Rece', 'Lanțul Cuvintelor', 'Conexiuni', 'Intrusul'],
  'sense': 'Mașină de găurit materiale cu un burghiu rotitor;mașină de găurit este sinonim '
           'substituibil în acest sens.',
  'register': 'Selected everyday workshop/craft noun sense; unrelated,archaic/poetic-only meanings '
              'excluded;no instructions or clinical ruling.',
  'verified_forms': ['bormașină',
                     'bormașini',
                     'bormașinile',
                     'bormașinii',
                     'bormașinilor',
                     'mașină de găurit',
                     'mașini de găurit',
                     'mașinile de găurit',
                     'mașinii de găurit',
                     'mașinilor de găurit'],
  'proposed_forms': ['bormașină',
                     'bormașini',
                     'bormașinile',
                     'bormașinii',
                     'bormașinilor',
                     'mașină de găurit',
                     'mașini de găurit',
                     'mașinile de găurit',
                     'mașinii de găurit',
                     'mașinilor de găurit'],
  'already_resolved_forms': [],
  'already_reserved_forms': [],
  'excluded_form_hypotheses': [{'form': 'bormașinei',
                                'reason': 'Not selected DOOM3 bormașinii genitive;hypothesis '
                                          'excluded.'}],
  'dictionaries': [{'lemma': 'bormașină',
                    'url': 'https://dexonline.ro/definitie/borma%C8%99in%C4%83/json',
                    'dex_definition_ids': ['836410'],
                    'doom3_definition_ids': ['1319208'],
                    'flexion_url': 'https://dexonline.ro/definitie/borma%C8%99in%C4%83',
                    'flexion_authority': 'Explicit DOOM3 feminine bormașină table,not neuter '
                                         'bormașin variant',
                    'forms_note': 'bormașină/bormașina/bormașini/bormașinile/bormașinii/bormașinilor;exclude '
                                  'bormașinei.',
                    'paraphrase': 'Mașină de găurit materiale cu un burghiu rotitor;mașină de '
                                  'găurit este sinonim substituibil în acest sens.; selected DEX '
                                  'sense/register and DOOM3 lexical gender/number checked, '
                                  'ordinary forms from Explicit DOOM3 feminine bormașină table,not '
                                  'neuter bormașin variant.'},
                   {'lemma': 'mașină',
                    'url': 'https://dexonline.ro/definitie/ma%C8%99in%C4%83/json',
                    'dex_definition_ids': ['886160'],
                    'doom3_definition_ids': ['1291361'],
                    'flexion_url': 'https://dexonline.ro/definitie/ma%C8%99in%C4%83',
                    'flexion_authority': 'Explicit DOOM3 feminine mașină table;only qualified de '
                                         'găurit inputs admitted',
                    'forms_note': 'Qualified mașină de găurit/mașina de găurit/mașini de '
                                  'găurit/mașinile de găurit/mașinii de găurit/mașinilor de '
                                  'găurit;bare head remains automobile owner.',
                    'paraphrase': 'Mașină de găurit materiale cu un burghiu rotitor;mașină de '
                                  'găurit este sinonim substituibil în acest sens.; selected DEX '
                                  'sense/register and DOOM3 lexical gender/number checked, '
                                  'ordinary forms from Explicit DOOM3 feminine mașină table;only '
                                  'qualified de găurit inputs admitted.'}],
  'sources': [{'url': 'https://dexonline.ro/definitie/borma%C8%99in%C4%83/json',
               'paraphrase': 'Mașină de găurit materiale cu un burghiu rotitor;mașină de găurit '
                             'este sinonim substituibil în acest sens.; selected DEX '
                             'sense/register and DOOM3 lexical gender/number checked, ordinary '
                             'forms from Explicit DOOM3 feminine bormașină table,not neuter '
                             'bormașin variant.'},
              {'url': 'https://dexonline.ro/definitie/ma%C8%99in%C4%83/json',
               'paraphrase': 'Mașină de găurit materiale cu un burghiu rotitor;mașină de găurit '
                             'este sinonim substituibil în acest sens.; selected DEX '
                             'sense/register and DOOM3 lexical gender/number checked, ordinary '
                             'forms from Explicit DOOM3 feminine mașină table;only qualified de '
                             'găurit inputs admitted.'},
              {'url': 'https://ro.wiktionary.org/wiki/borma%C8%99in%C4%83',
               'paraphrase': 'Confirmă definiția prin mașină de găurit și paradigma feminină '
                             'bormașinii/bormașini.'},
              {'url': 'https://www.bosch-diy.com/ro/ro/p/advancedimpact-900-0603174020',
               'paraphrase': 'Producătorul descrie un exemplu electric de mașină de găurit pentru '
                             'lemn și zidărie;nu se preiau valorile numerice sau recomandările.'}],
  'link_targets': [{'node_id': 'n_v1_19_burghiu',
                    'label': 'Burghiu',
                    'category': 'viata_de_roman',
                    'status': 'batch',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'poate roti un burghiu',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_bormasina',
                    'edge_dst': 'n_v1_19_burghiu',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://dexonline.ro/definitie/borma%C8%99in%C4%83/json'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v3sti_electricitate',
                    'label': 'Electricitate',
                    'category': 'stiinta',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'modelele electrice folosesc electricitate',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_bormasina',
                    'edge_dst': 'n_v3sti_electricitate',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://www.bosch-diy.com/ro/ro/p/advancedimpact-900-0603174020'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v1_3_material_lemn',
                    'label': 'Lemn',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'poate găuri lemnul cu un burghiu potrivit',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_bormasina',
                    'edge_dst': 'n_v1_3_material_lemn',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://www.bosch-diy.com/ro/ro/p/advancedimpact-900-0603174020'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v24_home_structure_perete',
                    'label': 'Perete',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'poate găuri pereții cu un burghiu potrivit',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_bormasina',
                    'edge_dst': 'n_v24_home_structure_perete',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://www.bosch-diy.com/ro/ro/p/advancedimpact-900-0603174020'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'}],
  'author_supported_exact_sense_synonym': 'Mașină de găurit (qualified forms only);DEX explicitly '
                                          'equates the drilling-machine sense;formal reviewers '
                                          'still required.',
  'source_quality_warnings': ['The manufacturer page contains differing numeric power/depth '
                              'blocks;no numeric specification is adopted.'],
  'current_graph_counts': {'distinct': 4, 'old_main': 3, 'same_category': 3, 'batch': 1},
  'frequency': {'url': 'https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/ro/ro_50k.txt',
                'best_rank': None,
                'matched_form': None,
                'role': 'Positive signal only; absence does not reject concrete everyday/school '
                        'vocabulary.'},
  'scope': 'Accepted after both once-only independent whole-batch web reviews and explicit verdict '
           'application;reviewed/unapplied/not_landed. No game round,target,recipe,route or '
           'runtime qualification.',
  'review_verdicts': {'factual': {'verdict': 'accept',
                                  'rationale': 'Mașină de găurit este substituibil în sensul '
                                               'mecanismului cu burghiu; formele feminine sunt '
                                               'confirmate și toate intrările Mașină sunt '
                                               'calificate.'},
                      'quality': {'verdict': 'accept',
                                  'rationale': 'Familiar household drill; mașină de găurit '
                                               'substitutes in this exact sense and its complete '
                                               'qualified family leaves bare car forms '
                                               'untouched.'}}},
 {'id': 'v119-mistrie',
  'lemma': 'Mistrie',
  'kind': 'new_shared_concept',
  'node_id': 'n_v1_19_mistrie',
  'games': ['Cald sau Rece', 'Lanțul Cuvintelor', 'Conexiuni', 'Intrusul', 'Perechi'],
  'sense': 'Unealtă de zidărie cu lamă de oțel și mâner,pentru întinderea mortarului pe zid.',
  'register': 'Selected everyday workshop/craft noun sense; unrelated,archaic/poetic-only meanings '
              'excluded;no instructions or clinical ruling.',
  'verified_forms': ['mistrie', 'mistria', 'mistrii', 'mistriile', 'mistriei', 'mistriilor'],
  'proposed_forms': ['mistrie', 'mistria', 'mistrii', 'mistriile', 'mistriei', 'mistriilor'],
  'already_resolved_forms': [],
  'already_reserved_forms': [],
  'excluded_form_hypotheses': [],
  'dictionaries': [{'lemma': 'mistrie',
                    'url': 'https://dexonline.ro/definitie/mistrie/json',
                    'dex_definition_ids': ['890809'],
                    'doom3_definition_ids': ['1294000'],
                    'flexion_url': 'https://dexonline.ro/definitie/mistrie',
                    'flexion_authority': 'DOOM3 mistria/mistriei/mistrii/mistriile plus matching '
                                         'DOR feminine noun table',
                    'forms_note': 'mistrie/mistria/mistrii/mistriile/mistriei/mistriilor;no '
                                  'regional mestrie/mistirie or vocatives.',
                    'paraphrase': 'Unealtă de zidărie cu lamă de oțel și mâner,pentru întinderea '
                                  'mortarului pe zid.; selected DEX sense/register and DOOM3 '
                                  'lexical gender/number checked, ordinary forms from DOOM3 '
                                  'mistria/mistriei/mistrii/mistriile plus matching DOR feminine '
                                  'noun table.'}],
  'sources': [{'url': 'https://dexonline.ro/definitie/mistrie/json',
               'paraphrase': 'Unealtă de zidărie cu lamă de oțel și mâner,pentru întinderea '
                             'mortarului pe zid.; selected DEX sense/register and DOOM3 lexical '
                             'gender/number checked, ordinary forms from DOOM3 '
                             'mistria/mistriei/mistrii/mistriile plus matching DOR feminine noun '
                             'table.'},
              {'url': 'https://ro.wiktionary.org/wiki/mistrie',
               'paraphrase': 'Confirmă unealta de zidărie din oțel și paradigma feminină '
                             'obișnuită.'},
              {'url': 'https://www.dedeman.ro/ro/mistrie-trapez-holzer-602-otel-20-cm/p/5011948',
               'paraphrase': 'Descrierea propriei mistrii Holzer602 confirmă lama din oțel,mânerul '
                             'din lemn și folosirea la întinderea mortarelor;nu se adoptă '
                             'recomandări sau dimensiuni.'}],
  'link_targets': [{'node_id': 'n_v1_19_mortar',
                    'label': 'Mortar',
                    'category': 'viata_de_roman',
                    'status': 'batch',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'întinde mortarul la zidărie',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_mistrie',
                    'edge_dst': 'n_v1_19_mortar',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://dexonline.ro/definitie/mistrie/json',
                                'https://www.dedeman.ro/ro/mistrie-trapez-holzer-602-otel-20-cm/p/5011948'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v24_home_structure_perete',
                    'label': 'Perete',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'poate fi folosită la zidirea unui perete',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_mistrie',
                    'edge_dst': 'n_v24_home_structure_perete',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://dexonline.ro/definitie/mistrie/json'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v1_3_material_lemn',
                    'label': 'Lemn',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'mânerul său poate fi din lemn',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_mistrie',
                    'edge_dst': 'n_v1_3_material_lemn',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://www.dedeman.ro/ro/mistrie-trapez-holzer-602-otel-20-cm/p/5011948'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v4sti_metal',
                    'label': 'metal',
                    'category': 'stiinta',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'are o lamă din metal',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_mistrie',
                    'edge_dst': 'n_v4sti_metal',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://dexonline.ro/definitie/mistrie/json',
                                'https://ro.wiktionary.org/wiki/mistrie',
                                'https://www.dedeman.ro/ro/mistrie-trapez-holzer-602-otel-20-cm/p/5011948'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'}],
  'current_graph_counts': {'distinct': 5, 'old_main': 3, 'same_category': 3, 'batch': 2},
  'frequency': {'url': 'https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/ro/ro_50k.txt',
                'best_rank': None,
                'matched_form': None,
                'role': 'Positive signal only; absence does not reject concrete everyday/school '
                        'vocabulary.'},
  'scope': 'Accepted after both once-only independent whole-batch web reviews and explicit verdict '
           'application;reviewed/unapplied/not_landed. No game round,target,recipe,route or '
           'runtime qualification.',
  'review_verdicts': {'factual': {'verdict': 'accept',
                                  'rationale': 'Unealta de zidărie pentru mortar și familia '
                                               'mistria/mistriei/mistrii sunt confirmate; '
                                               'utilizările materialelor sunt calificate.'},
                      'quality': {'verdict': 'accept',
                                  'rationale': 'The masonry trowel is named in a Romanian '
                                               'education curriculum and a current mortar '
                                               'producer; description and full family are fair.'}}},
 {'id': 'v119-ruleta',
  'lemma': 'Ruletă',
  'kind': 'new_shared_concept',
  'node_id': 'n_v1_19_ruleta',
  'games': ['Cald sau Rece', 'Lanțul Cuvintelor', 'Conexiuni', 'Intrusul'],
  'sense': 'Instrument cu bandă gradată rulabilă pentru măsurarea lungimilor;excluse jocul de '
           'noroc și rotița pentru tipare sau aluat.',
  'register': 'Selected everyday workshop/craft noun sense; unrelated,archaic/poetic-only meanings '
              'excluded;no instructions or clinical ruling.',
  'verified_forms': ['ruletă', 'rulete', 'ruletele', 'ruletei', 'ruletelor'],
  'proposed_forms': ['ruletă', 'rulete', 'ruletele', 'ruletei', 'ruletelor'],
  'already_resolved_forms': [],
  'already_reserved_forms': [],
  'excluded_form_hypotheses': [],
  'dictionaries': [{'lemma': 'ruletă',
                    'url': 'https://dexonline.ro/definitie/rulet%C4%83/json',
                    'dex_definition_ids': ['859899'],
                    'doom3_definition_ids': ['1314868'],
                    'flexion_url': 'https://dexonline.ro/definitie/rulet%C4%83',
                    'flexion_authority': 'DOOM3 feminine ruletei/rulete plus matching DOR noun '
                                         'table',
                    'forms_note': 'ruletă/ruleta/rulete/ruletele/ruletei/ruletelor;one spelling '
                                  'per folded key;no gambling or cutting-wheel sense.',
                    'paraphrase': 'Instrument cu bandă gradată rulabilă pentru măsurarea '
                                  'lungimilor;excluse jocul de noroc și rotița pentru tipare sau '
                                  'aluat.; selected DEX sense/register and DOOM3 lexical '
                                  'gender/number checked, ordinary forms from DOOM3 feminine '
                                  'ruletei/rulete plus matching DOR noun table.'}],
  'sources': [{'url': 'https://dexonline.ro/definitie/rulet%C4%83/json',
               'paraphrase': 'Instrument cu bandă gradată rulabilă pentru măsurarea '
                             'lungimilor;excluse jocul de noroc și rotița pentru tipare sau '
                             'aluat.; selected DEX sense/register and DOOM3 lexical gender/number '
                             'checked, ordinary forms from DOOM3 feminine ruletei/rulete plus '
                             'matching DOR noun table.'},
              {'url': 'https://ro.wiktionary.org/wiki/rulet%C4%83',
               'paraphrase': 'Confirmă sensul de măsurare și paradigma feminină ruletei/rulete.'},
              {'url': 'https://ro.wikipedia.org/wiki/Rigl%C4%83',
               'paraphrase': 'Descrie rigla ca instrument pentru măsurarea distanțelor și '
                             'menționează ruleta retractabilă.'},
              {'url': 'https://www.leroymerlin.ro/inspiratie/materiale-de-constructii-tamplarie/cum-se-calculeaza-metrul-patrat-formula-de-calcul-si-instrumente-necesare.html',
               'paraphrase': 'Secțiunea despre instrumente indică ruleta și rigla pentru măsurări '
                             'verticale/orizontale;contextul include pereți și pardoseli.'}],
  'link_targets': [{'node_id': 'n_v24_school_supplies_rigla',
                    'label': 'Riglă',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'măsoară lungimi, la fel ca rigla',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_ruleta',
                    'edge_dst': 'n_v24_school_supplies_rigla',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://ro.wikipedia.org/wiki/Rigl%C4%83',
                                'https://www.leroymerlin.ro/inspiratie/materiale-de-constructii-tamplarie/cum-se-calculeaza-metrul-patrat-formula-de-calcul-si-instrumente-necesare.html',
                                'https://dexonline.ro/definitie/rulet%C4%83/json'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v24_home_structure_perete',
                    'label': 'Perete',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'poate măsura dimensiunile unui perete',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_ruleta',
                    'edge_dst': 'n_v24_home_structure_perete',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://www.leroymerlin.ro/inspiratie/materiale-de-constructii-tamplarie/cum-se-calculeaza-metrul-patrat-formula-de-calcul-si-instrumente-necesare.html'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v24_home_surfaces_podea',
                    'label': 'Podea',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'poate măsura dimensiunile unei podele',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_ruleta',
                    'edge_dst': 'n_v24_home_surfaces_podea',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://www.leroymerlin.ro/inspiratie/materiale-de-constructii-tamplarie/cum-se-calculeaza-metrul-patrat-formula-de-calcul-si-instrumente-necesare.html'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v4sti_metal',
                    'label': 'metal',
                    'category': 'stiinta',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'banda unor modele este din metal',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_ruleta',
                    'edge_dst': 'n_v4sti_metal',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://dexonline.ro/definitie/rulet%C4%83/json'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'}],
  'source_acquisition_note': 'Leroy Merlin direct request returned403;complete article read via '
                             'web reader,especially instrument section66–67 and wall/floor '
                             'contexts.',
  'source_quality_warnings': ['No mathematical conversion,coverage quantity,cost or recommendation '
                              'from the guide is adopted;only the measuring-tool use is retained.'],
  'current_graph_counts': {'distinct': 4, 'old_main': 4, 'same_category': 3, 'batch': 0},
  'frequency': {'url': 'https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/ro/ro_50k.txt',
                'best_rank': 29437,
                'matched_form': 'ruletă',
                'role': 'Positive signal only; absence does not reject concrete everyday/school '
                        'vocabulary.'},
  'scope': 'Accepted after both once-only independent whole-batch web reviews and explicit verdict '
           'application;reviewed/unapplied/not_landed. No game round,target,recipe,route or '
           'runtime qualification.',
  'review_verdicts': {'factual': {'verdict': 'accept',
                                  'rationale': 'Este selectat instrumentul de măsurare, nu jocul '
                                               'de noroc; paradigma feminină și folosirea la '
                                               'dimensiuni sunt confirmate.'},
                      'quality': {'verdict': 'accept',
                                  'rationale': 'A familiar measuring tape, present in practical '
                                               'school material and household measuring guidance; '
                                               'gambling and pastry-wheel senses stay excluded.'}}},
 {'id': 'v119-topor',
  'lemma': 'Topor',
  'kind': 'new_shared_concept',
  'node_id': 'n_v1_19_topor',
  'games': ['Cald sau Rece', 'Lanțul Cuvintelor', 'Conexiuni', 'Intrusul'],
  'sense': 'Unealtă cu tăiș pentru tăiat copaci și despicat lemne;fără sens figurat sau de armă.',
  'register': 'Selected everyday workshop/craft noun sense; unrelated,archaic/poetic-only meanings '
              'excluded;no instructions or clinical ruling.',
  'verified_forms': ['topor', 'toporul', 'topoare', 'topoarele', 'toporului', 'topoarelor'],
  'proposed_forms': ['topor', 'toporul', 'topoare', 'topoarele', 'toporului', 'topoarelor'],
  'already_resolved_forms': [],
  'already_reserved_forms': [],
  'excluded_form_hypotheses': [],
  'dictionaries': [{'lemma': 'topor',
                    'url': 'https://dexonline.ro/definitie/topor/json',
                    'dex_definition_ids': ['834133'],
                    'doom3_definition_ids': ['1269305'],
                    'flexion_url': 'https://dexonline.ro/definitie/topor',
                    'flexion_authority': 'DOOM3 neuter topoare entry plus matching DOR noun table',
                    'forms_note': 'topor/toporul/topoare/topoarele/toporului/topoarelor;no '
                                  'elisions,vocatives or regional synonym inputs.',
                    'paraphrase': 'Unealtă cu tăiș pentru tăiat copaci și despicat lemne;fără sens '
                                  'figurat sau de armă.; selected DEX sense/register and DOOM3 '
                                  'lexical gender/number checked, ordinary forms from DOOM3 neuter '
                                  'topoare entry plus matching DOR noun table.'}],
  'sources': [{'url': 'https://dexonline.ro/definitie/topor/json',
               'paraphrase': 'Unealtă cu tăiș pentru tăiat copaci și despicat lemne;fără sens '
                             'figurat sau de armă.; selected DEX sense/register and DOOM3 lexical '
                             'gender/number checked, ordinary forms from DOOM3 neuter topoare '
                             'entry plus matching DOR noun table.'},
              {'url': 'https://ro.wiktionary.org/wiki/topor',
               'paraphrase': 'Confirmă tăierea lemnului,corpul de oțel și paradigma neutră '
                             'topoare.'},
              {'url': 'https://www.gardena.com/ro/produse/copac-arbust-ingrijire/topoare/toporisca-universala-900b/967330201.html',
               'paraphrase': 'Producătorul numește toporișca o variantă mică de topor și o leagă '
                             'de lemn și activități în grădină.'},
              {'url': 'https://www.gardena.com/ro/produse/copac-arbust-ingrijire/ferastraie-ferastrau-de-gradina/ferastrau-pentru-gradinar-300-p/967238601.html',
               'paraphrase': 'Pagina fierăstrăului pentru grădinar confirmă aceeași funcție de '
                             'tăiere a lemnului;nu se preiau recomandări.'},
              {'url': 'https://dexonline.ro/definitie/fier%C4%83str%C4%83u/json',
               'paraphrase': 'Definiția DEX exactă a fierăstrăului confirmă tăierea lemnului;izvor '
                             'proaspăt verificat de ambii recenzori.'}],
  'link_targets': [{'node_id': 'n_v4sti_metal',
                    'label': 'metal',
                    'category': 'stiinta',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'are o parte tăietoare din metal',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_topor',
                    'edge_dst': 'n_v4sti_metal',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://dexonline.ro/definitie/topor/json'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v1_3_material_lemn',
                    'label': 'Lemn',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'poate tăia sau despica lemnul',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_topor',
                    'edge_dst': 'n_v1_3_material_lemn',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://dexonline.ro/definitie/topor/json',
                                'https://www.gardena.com/ro/produse/copac-arbust-ingrijire/topoare/toporisca-universala-900b/967330201.html'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v32_workshop_cut_fierastrau',
                    'label': 'Fierăstrău',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'are în comun cu fierăstrăul tăierea lemnului',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_topor',
                    'edge_dst': 'n_v32_workshop_cut_fierastrau',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://dexonline.ro/definitie/topor/json',
                                'https://dexonline.ro/definitie/fier%C4%83str%C4%83u/json'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v24_home_outdoor_gradina',
                    'label': 'Grădină',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'poate fi folosit la lucrări cu lemnul în grădină',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_topor',
                    'edge_dst': 'n_v24_home_outdoor_gradina',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://www.gardena.com/ro/produse/copac-arbust-ingrijire/topoare/toporisca-universala-900b/967330201.html'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'}],
  'current_graph_counts': {'distinct': 4, 'old_main': 4, 'same_category': 3, 'batch': 0},
  'frequency': {'url': 'https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/ro/ro_50k.txt',
                'best_rank': 12675,
                'matched_form': 'topor',
                'role': 'Positive signal only; absence does not reject concrete everyday/school '
                        'vocabulary.'},
  'scope': 'Accepted after both once-only independent whole-batch web reviews and explicit verdict '
           'application;reviewed/unapplied/not_landed. No game round,target,recipe,route or '
           'runtime qualification.',
  'review_corrections': [{'kind': 'replace_edge_source_binding',
                          'src': 'n_v1_19_topor',
                          'dst': 'n_v32_workshop_cut_fierastrau',
                          'relation': 'related_to',
                          'before': ['https://dexonline.ro/definitie/topor/json',
                                     'https://www.gardena.com/ro/produse/copac-arbust-ingrijire/ferastraie-ferastrau-de-gradina/ferastrau-pentru-gradinar-300-p/967238601.html'],
                          'after': ['https://dexonline.ro/definitie/topor/json',
                                    'https://dexonline.ro/definitie/fier%C4%83str%C4%83u/json'],
                          'reviewers': ['factual', 'quality']}],
  'fresh_review_source_binding_notes': ['The exact correction above supplies the current reviewed '
                                        'edge authority; earlier acquisition notes describe '
                                        'historical author research and do not override the fresh '
                                        'binding.'],
  'review_verdicts': {'factual': {'verdict': 'modify',
                                  'rationale': 'Sensul de unealtă pentru lemn și familia topoare '
                                               'sunt confirmate; corectați numai legarea dovezilor '
                                               'muchiei către Fierăstrău conform '
                                               'required_changes.'},
                      'quality': {'verdict': 'modify',
                                  'rationale': 'School woodworking and current garden-tool usage '
                                               'support recognition; keep the wood-cutting analogy '
                                               'only with the executable source-binding '
                                               'correction.'}}},
 {'id': 'v119-baros',
  'lemma': 'Baros',
  'kind': 'new_shared_concept',
  'node_id': 'n_v1_19_baros',
  'games': ['Cald sau Rece', 'Lanțul Cuvintelor', 'Conexiuni', 'Intrusul'],
  'sense': 'Ciocan mare și greu pentru lucrări de fierărie sau construcții;fără sens ori folosire '
           'de armă.',
  'register': 'Selected everyday workshop/craft noun sense; unrelated,archaic/poetic-only meanings '
              'excluded;no instructions or clinical ruling.',
  'verified_forms': ['baros', 'barosul', 'baroase', 'baroasele', 'barosului', 'baroaselor'],
  'proposed_forms': ['baros', 'barosul', 'baroase', 'baroasele', 'barosului', 'baroaselor'],
  'already_resolved_forms': [],
  'already_reserved_forms': [],
  'excluded_form_hypotheses': [{'form': 'baroși',
                                'reason': 'Not selected DOOM3 neuter baroase paradigm;masculine '
                                          'hypothesis excluded.'},
                               {'form': 'baroșii',
                                'reason': 'Not selected DOOM3 neuter baroase paradigm;masculine '
                                          'hypothesis excluded.'},
                               {'form': 'baroșilor',
                                'reason': 'Not selected DOOM3 neuter baroase paradigm;masculine '
                                          'hypothesis excluded.'}],
  'dictionaries': [{'lemma': 'baros',
                    'url': 'https://dexonline.ro/definitie/baros/json',
                    'dex_definition_ids': ['832992'],
                    'doom3_definition_ids': ['1317413'],
                    'flexion_url': 'https://dexonline.ro/definitie/baros',
                    'flexion_authority': 'Explicit DOOM3 neuter baroase table,not DOR -uri or '
                                         'masculine hypotheses',
                    'forms_note': 'baros/barosul/baroase/baroasele/barosului/baroaselor;no '
                                  '-uri,-i,elisions or vocatives.',
                    'paraphrase': 'Ciocan mare și greu pentru lucrări de fierărie sau '
                                  'construcții;fără sens ori folosire de armă.; selected DEX '
                                  'sense/register and DOOM3 lexical gender/number checked, '
                                  'ordinary forms from Explicit DOOM3 neuter baroase table,not DOR '
                                  '-uri or masculine hypotheses.'}],
  'sources': [{'url': 'https://dexonline.ro/definitie/baros/json',
               'paraphrase': 'Ciocan mare și greu pentru lucrări de fierărie sau construcții;fără '
                             'sens ori folosire de armă.; selected DEX sense/register and DOOM3 '
                             'lexical gender/number checked, ordinary forms from Explicit DOOM3 '
                             'neuter baroase table,not DOR -uri or masculine hypotheses.'},
              {'url': 'https://ro.wiktionary.org/wiki/baros',
               'paraphrase': 'Confirmă ciocanul mare;dintre paradigmele prezentate se selectează '
                             'numai DOOM3 baroase.'},
              {'url': 'https://www.dedeman.ro/ro/baros-pentru-constructii-dupu-coada-din-lemn-900-mm-5-kg/p/1034802',
               'paraphrase': 'Descrierea produsului Dupu confirmă coada de lemn și folosirea la '
                             'sfărâmarea pietrelor.'},
              {'url': 'https://www.dedeman.ro/ro/baros-pentru-constructii-holzer-it301905000-coada-din-lemn-900-mm-5-kg/p/1036552',
               'paraphrase': 'Descrierea produsului Holzer confirmă corpul de oțel și coada de '
                             'lemn;valorile numerice nu sunt adoptate.'}],
  'link_targets': [{'node_id': 'n_v32_workshop_hand_ciocan',
                    'label': 'Ciocan',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'is_a',
                    'claim_to_verify': 'este un ciocan mare și greu',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_baros',
                    'edge_dst': 'n_v32_workshop_hand_ciocan',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://dexonline.ro/definitie/baros/json'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v4sti_metal',
                    'label': 'metal',
                    'category': 'stiinta',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'are un cap din metal',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_baros',
                    'edge_dst': 'n_v4sti_metal',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://www.dedeman.ro/ro/baros-pentru-constructii-holzer-it301905000-coada-din-lemn-900-mm-5-kg/p/1036552'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v1_3_material_lemn',
                    'label': 'Lemn',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'coada sa poate fi din lemn',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_baros',
                    'edge_dst': 'n_v1_3_material_lemn',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://www.dedeman.ro/ro/baros-pentru-constructii-dupu-coada-din-lemn-900-mm-5-kg/p/1034802',
                                'https://www.dedeman.ro/ro/baros-pentru-constructii-holzer-it301905000-coada-din-lemn-900-mm-5-kg/p/1036552'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v28_nature_material_piatra',
                    'label': 'Piatră',
                    'category': 'stiinta',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'poate sparge piatra prin lovire',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_baros',
                    'edge_dst': 'n_v28_nature_material_piatra',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://www.dedeman.ro/ro/baros-pentru-constructii-dupu-coada-din-lemn-900-mm-5-kg/p/1034802'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'}],
  'current_graph_counts': {'distinct': 4, 'old_main': 4, 'same_category': 2, 'batch': 0},
  'frequency': {'url': 'https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/ro/ro_50k.txt',
                'best_rank': 45526,
                'matched_form': 'baros',
                'role': 'Positive signal only; absence does not reject concrete everyday/school '
                        'vocabulary.'},
  'scope': 'Accepted after both once-only independent whole-batch web reviews and explicit verdict '
           'application;reviewed/unapplied/not_landed. No game round,target,recipe,route or '
           'runtime qualification.',
  'review_verdicts': {'factual': {'verdict': 'accept',
                                  'rationale': 'Ciocanul greu are plural normativ baroase; există '
                                               'exemple primare pentru capul metalic, coada de '
                                               'lemn și spargerea pietrei.'},
                      'quality': {'verdict': 'accept',
                                  'rationale': 'A concrete heavy hammer in current Romanian trade '
                                               'catalogues and the wider traditional workshop '
                                               'context; lower frequency does not make it '
                                               'unsuitable vocabulary.'}}},
 {'id': 'v119-nicovala',
  'lemma': 'Nicovală',
  'kind': 'new_shared_concept',
  'node_id': 'n_v1_19_nicovala',
  'games': ['Cald sau Rece', 'Lanțul Cuvintelor', 'Conexiuni', 'Intrusul'],
  'sense': 'Unealtă de forjă pentru sprijinirea pieselor de metal lovite cu ciocanul;exclus osul '
           'urechii.',
  'register': 'Selected everyday workshop/craft noun sense; unrelated,archaic/poetic-only meanings '
              'excluded;no instructions or clinical ruling.',
  'verified_forms': ['nicovală', 'nicovale', 'nicovalele', 'nicovalei', 'nicovalelor'],
  'proposed_forms': ['nicovală', 'nicovale', 'nicovalele', 'nicovalei', 'nicovalelor'],
  'already_resolved_forms': [],
  'already_reserved_forms': [],
  'excluded_form_hypotheses': [],
  'dictionaries': [{'lemma': 'nicovală',
                    'url': 'https://dexonline.ro/definitie/nicoval%C4%83/json',
                    'dex_definition_ids': ['884384'],
                    'doom3_definition_ids': ['1290099'],
                    'flexion_url': 'https://dexonline.ro/definitie/nicoval%C4%83',
                    'flexion_authority': 'DOOM3 feminine nicovalei/nicovale plus matching DOR noun '
                                         'table',
                    'forms_note': 'nicovală/nicovala/nicovale/nicovalele/nicovalei/nicovalelor;no '
                                  'regional variants or anatomical sense.',
                    'paraphrase': 'Unealtă de forjă pentru sprijinirea pieselor de metal lovite cu '
                                  'ciocanul;exclus osul urechii.; selected DEX sense/register and '
                                  'DOOM3 lexical gender/number checked, ordinary forms from DOOM3 '
                                  'feminine nicovalei/nicovale plus matching DOR noun table.'}],
  'sources': [{'url': 'https://dexonline.ro/definitie/nicoval%C4%83/json',
               'paraphrase': 'Unealtă de forjă pentru sprijinirea pieselor de metal lovite cu '
                             'ciocanul;exclus osul urechii.; selected DEX sense/register and DOOM3 '
                             'lexical gender/number checked, ordinary forms from DOOM3 feminine '
                             'nicovalei/nicovale plus matching DOR noun table.'},
              {'url': 'https://ro.wiktionary.org/wiki/nicoval%C4%83',
               'paraphrase': 'Secțiunea de unealtă și paradigma nicovalei/nicovale sunt '
                             'confirmate;omonimul anatomic nu este selectat.'},
              {'url': 'https://ro.wikipedia.org/wiki/Nicoval%C4%83',
               'paraphrase': 'Confirmă sprijinirea pieselor metalice la baterea cu ciocanul.'},
              {'url': 'https://biblioteca-digitala.ro/reviste/carte/brasov-muzeu/NEGULICI_Feronerie-brasoveana-XV-XIX_2003.pdf',
               'paraphrase': 'Catalogul muzeal descrie un fierar care bate pe nicovală o potcoavă '
                             'ținută cu cleștele.'},
              {'url': 'https://www.rri.ro/rubrici/vizitati-romania/muzeul-satului-isverna-id591495.html',
               'paraphrase': 'Reportajul propriu Radio România prezintă un fierar care folosește '
                             'nicovala în atelier;nu se preiau nume,date sau temperaturi.'},
              {'url': 'https://analelebanatului.ro/static/media/articles/2022/01/19/08_tanase.pdf',
               'paraphrase': 'Articolul muzeal descrie ținerea piesei pe nicovală cu '
                             'cleștele;izvor proaspăt verificat de recenzorul de calitate.'}],
  'link_targets': [{'node_id': 'n_v4sti_metal',
                    'label': 'metal',
                    'category': 'stiinta',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'pe ea se pot prelucra piese din metal',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_nicovala',
                    'edge_dst': 'n_v4sti_metal',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://dexonline.ro/definitie/nicoval%C4%83/json',
                                'https://ro.wikipedia.org/wiki/Nicoval%C4%83'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v32_workshop_hand_ciocan',
                    'label': 'Ciocan',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'susține piesa lovită cu ciocanul',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_nicovala',
                    'edge_dst': 'n_v32_workshop_hand_ciocan',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://dexonline.ro/definitie/nicoval%C4%83/json',
                                'https://ro.wikipedia.org/wiki/Nicoval%C4%83'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v1_19_fierar',
                    'label': 'Fierar',
                    'category': 'societate',
                    'status': 'batch',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'poate prelucra piesa pe nicovală',
                    'direction': 'incoming',
                    'edge_src': 'n_v1_19_fierar',
                    'edge_dst': 'n_v1_19_nicovala',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://biblioteca-digitala.ro/reviste/carte/brasov-muzeu/NEGULICI_Feronerie-brasoveana-XV-XIX_2003.pdf',
                                'https://www.rri.ro/rubrici/vizitati-romania/muzeul-satului-isverna-id591495.html'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v32_workshop_hand_cleste',
                    'label': 'Clește',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'piesa de pe nicovală poate fi ținută cu un clește',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_nicovala',
                    'edge_dst': 'n_v32_workshop_hand_cleste',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://analelebanatului.ro/static/media/articles/2022/01/19/08_tanase.pdf'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'}],
  'source_acquisition_note': 'Museum primary passage read through indexed excerpt;direct status '
                             'recorded in trace.',
  'source_quality_warnings': ['Unrelated anatomical definition has a wrong ear-ossicle count;no '
                              'anatomical fact or number adopted.'],
  'current_graph_counts': {'distinct': 4, 'old_main': 3, 'same_category': 2, 'batch': 1},
  'frequency': {'url': 'https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/ro/ro_50k.txt',
                'best_rank': 47926,
                'matched_form': 'nicovală',
                'role': 'Positive signal only; absence does not reject concrete everyday/school '
                        'vocabulary.'},
  'scope': 'Accepted after both once-only independent whole-batch web reviews and explicit verdict '
           'application;reviewed/unapplied/not_landed. No game round,target,recipe,route or '
           'runtime qualification.',
  'review_corrections': [{'kind': 'replace_edge_source_binding',
                          'src': 'n_v1_19_nicovala',
                          'dst': 'n_v32_workshop_hand_cleste',
                          'relation': 'related_to',
                          'before': ['https://biblioteca-digitala.ro/reviste/carte/brasov-muzeu/NEGULICI_Feronerie-brasoveana-XV-XIX_2003.pdf'],
                          'after': ['https://analelebanatului.ro/static/media/articles/2022/01/19/08_tanase.pdf'],
                          'reviewers': ['quality']}],
  'fresh_review_source_binding_notes': ['The exact correction above supplies the current reviewed '
                                        'edge authority; earlier acquisition notes describe '
                                        'historical author research and do not override the fresh '
                                        'binding.'],
  'review_verdicts': {'factual': {'verdict': 'accept',
                                  'rationale': 'Este suportul de forjă, nu osul urechii; paradigma '
                                               'feminină și folosirea cu ciocan/clește sunt '
                                               'confirmate.'},
                      'quality': {'verdict': 'modify',
                                  'rationale': 'Cross-generational blacksmithing vocabulary with '
                                               'current Romanian cultural coverage; the tongs '
                                               'caption needs the precise freshly readable source '
                                               'binding.'}}},
 {'id': 'v119-menghina',
  'lemma': 'Menghină',
  'kind': 'new_shared_concept',
  'node_id': 'n_v1_19_menghina',
  'games': ['Cald sau Rece', 'Lanțul Cuvintelor', 'Conexiuni', 'Intrusul'],
  'sense': 'Dispozitiv cu fălci pentru fixarea pieselor ce urmează să fie prelucrate.',
  'register': 'Selected everyday workshop/craft noun sense; unrelated,archaic/poetic-only meanings '
              'excluded;no instructions or clinical ruling.',
  'verified_forms': ['menghină', 'menghine', 'menghinele', 'menghinei', 'menghinelor'],
  'proposed_forms': ['menghină', 'menghine', 'menghinele', 'menghinei', 'menghinelor'],
  'already_resolved_forms': [],
  'already_reserved_forms': [],
  'excluded_form_hypotheses': [],
  'dictionaries': [{'lemma': 'menghină',
                    'url': 'https://dexonline.ro/definitie/menghin%C4%83/json',
                    'dex_definition_ids': ['888278'],
                    'doom3_definition_ids': ['1292919'],
                    'flexion_url': 'https://dexonline.ro/definitie/menghin%C4%83',
                    'flexion_authority': 'DOOM3 feminine menghinei/menghine plus first matching '
                                         'DOR noun table,not menghinea/minghinea variants',
                    'forms_note': 'menghină/menghina/menghine/menghinele/menghinei/menghinelor;one '
                                  'spelling per folded key;no regional variants or vocatives.',
                    'paraphrase': 'Dispozitiv cu fălci pentru fixarea pieselor ce urmează să fie '
                                  'prelucrate.; selected DEX sense/register and DOOM3 lexical '
                                  'gender/number checked, ordinary forms from DOOM3 feminine '
                                  'menghinei/menghine plus first matching DOR noun table,not '
                                  'menghinea/minghinea variants.'}],
  'sources': [{'url': 'https://dexonline.ro/definitie/menghin%C4%83/json',
               'paraphrase': 'Dispozitiv cu fălci pentru fixarea pieselor ce urmează să fie '
                             'prelucrate.; selected DEX sense/register and DOOM3 lexical '
                             'gender/number checked, ordinary forms from DOOM3 feminine '
                             'menghinei/menghine plus first matching DOR noun table,not '
                             'menghinea/minghinea variants.'},
              {'url': 'https://ro.wiktionary.org/wiki/menghin%C4%83',
               'paraphrase': 'Confirmă dispozitivul de prindere și paradigma feminină '
                             'menghinei/menghine.'},
              {'url': 'https://www.dedeman.ro/ro/menghine/c/3861',
               'paraphrase': 'Pagina proprie a furnizorului precizează explicit imobilizarea '
                             'pieselor din lemn sau metal.'},
              {'url': 'https://spitalpneumoftiziologieaiud.ro/wp-content/uploads/2019/11/Caiet-de-instruire-practica-Domeniul-mecanica-notiuni-de-lacatuserie-generala.pdf',
               'paraphrase': 'Caietul primar citit în cache,p41–42,arată fixarea materialului în '
                             'menghina fierăstrăului;capitolul de pilire folosește aceeași '
                             'fixare.'},
              {'url': 'https://www.autocv.ro/wp-content/uploads/2020/03/pilirea-metalelor-clasa-a-9-a-M2.pdf',
               'paraphrase': 'Pasajul primar indexat despre pilire descrie fixarea piesei în '
                             'menghină.'}],
  'link_targets': [{'node_id': 'n_v4sti_metal',
                    'label': 'metal',
                    'category': 'stiinta',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'poate fixa piese din metal',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_menghina',
                    'edge_dst': 'n_v4sti_metal',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://www.dedeman.ro/ro/menghine/c/3861'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v1_3_material_lemn',
                    'label': 'Lemn',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'poate fixa piese din lemn',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_menghina',
                    'edge_dst': 'n_v1_3_material_lemn',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://www.dedeman.ro/ro/menghine/c/3861'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v32_workshop_cut_fierastrau',
                    'label': 'Fierăstrău',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'poate ține piesa în timpul tăierii cu fierăstrăul',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_menghina',
                    'edge_dst': 'n_v32_workshop_cut_fierastrau',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://spitalpneumoftiziologieaiud.ro/wp-content/uploads/2019/11/Caiet-de-instruire-practica-Domeniul-mecanica-notiuni-de-lacatuserie-generala.pdf'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v1_19_pila',
                    'label': 'Pilă',
                    'category': 'viata_de_roman',
                    'status': 'batch',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'piesa pilită poate fi fixată într-o menghină',
                    'direction': 'incoming',
                    'edge_src': 'n_v1_19_pila',
                    'edge_dst': 'n_v1_19_menghina',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://spitalpneumoftiziologieaiud.ro/wp-content/uploads/2019/11/Caiet-de-instruire-practica-Domeniul-mecanica-notiuni-de-lacatuserie-generala.pdf',
                                'https://www.autocv.ro/wp-content/uploads/2020/03/pilirea-metalelor-clasa-a-9-a-M2.pdf'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'}],
  'source_acquisition_note': 'Supplier HTML fetched directly;Caiet direct PDF text reused from '
                             'tick1;AUTOCV passage through indexed primary reader. Saw example is '
                             'band/reciprocating machinery within the broad served saw concept,not '
                             'a claim that every handsaw carries a vise.',
  'current_graph_counts': {'distinct': 4, 'old_main': 3, 'same_category': 3, 'batch': 1},
  'frequency': {'url': 'https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/ro/ro_50k.txt',
                'best_rank': None,
                'matched_form': None,
                'role': 'Positive signal only; absence does not reject concrete everyday/school '
                        'vocabulary.'},
  'scope': 'Accepted after both once-only independent whole-batch web reviews and explicit verdict '
           'application;reviewed/unapplied/not_landed. No game round,target,recipe,route or '
           'runtime qualification.',
  'review_verdicts': {'factual': {'verdict': 'accept',
                                  'rationale': 'Dispozitivul de strângere cu fălci este sensul '
                                               'selectat; paradigma menghinei și utilizarea pentru '
                                               'piese sunt confirmate.'},
                      'quality': {'verdict': 'accept',
                                  'rationale': 'The vice is explicitly named in Romanian-language '
                                               'school/practical lessons; familiar workshop '
                                               'utility and the feminine paradigm are adequately '
                                               'supported.'}}},
 {'id': 'v119-adeziv',
  'lemma': 'Adeziv',
  'kind': 'new_shared_concept',
  'node_id': 'n_v1_19_adeziv',
  'games': ['Cald sau Rece', 'Lanțul Cuvintelor'],
  'sense': 'Substanță folosită pentru lipirea suprafețelor; substantivul masculin,nu adjectivul și '
           'nici aditivul agricol.',
  'register': 'Selected everyday workshop/craft noun sense; unrelated,archaic/poetic-only meanings '
              'excluded;no instructions or clinical ruling.',
  'verified_forms': ['adeziv', 'adezivul', 'adezivi', 'adezivii', 'adezivului', 'adezivilor'],
  'proposed_forms': ['adeziv', 'adezivul', 'adezivi', 'adezivii', 'adezivului', 'adezivilor'],
  'already_resolved_forms': [],
  'already_reserved_forms': [],
  'excluded_form_hypotheses': [{'form': 'adezive',
                                'reason': 'Forma adjectivală feminină,nu substantivul masculin '
                                          'selectat.'},
                               {'form': 'adezivele',
                                'reason': 'Forma adjectivală feminină,nu substantivul masculin '
                                          'selectat.'},
                               {'form': 'adezivelor',
                                'reason': 'Forma adjectivală feminină,nu substantivul masculin '
                                          'selectat.'}],
  'dictionaries': [{'lemma': 'adeziv',
                    'url': 'https://dexonline.ro/definitie/adeziv/json',
                    'dex_definition_ids': ['822979'],
                    'doom3_definition_ids': ['1321005'],
                    'flexion_url': 'https://dexonline.ro/definitie/adeziv',
                    'flexion_authority': 'DOR table explicitly labelled adeziv '
                                         '(substanță),substantiv masculin M1',
                    'forms_note': 'Six distinct ordinary noun keys;adjective '
                                  'table/vocative/elisions excluded.',
                    'paraphrase': 'Substanță folosită pentru lipirea suprafețelor; substantivul '
                                  'masculin,nu adjectivul și nici aditivul agricol.; selected DEX '
                                  'sense/register and DOOM3 lexical gender/number checked, '
                                  'ordinary forms from DOR table explicitly labelled adeziv '
                                  '(substanță),substantiv masculin M1.'}],
  'sources': [{'url': 'https://dexonline.ro/definitie/adeziv/json',
               'paraphrase': 'Substanță folosită pentru lipirea suprafețelor; substantivul '
                             'masculin,nu adjectivul și nici aditivul agricol.; selected DEX '
                             'sense/register and DOOM3 lexical gender/number checked, ordinary '
                             'forms from DOR table explicitly labelled adeziv '
                             '(substanță),substantiv masculin M1.'},
              {'url': 'https://ro.wiktionary.org/wiki/adeziv',
               'paraphrase': 'Substantiv masculin pentru produs de lipire,cu paradigma '
                             'adezivi/adezivului/adezivilor.'},
              {'url': 'https://catalog.temad.ro/adeziv-bicomponent-rapid-bison-epoxy-5-minute-4ml',
               'paraphrase': 'Catalogul distribuitorului include un adeziv destinat '
                             'lemnului,sticlei și cauciucului;nu se generalizează compatibilitatea '
                             'tuturor adezivilor.'},
              {'url': 'https://dexonline.ro/definitie/lipici/json',
               'paraphrase': 'DEX 864570,sensul1 Lipici: substanță pentru lipirea hârtiei,nu '
                             'plantele sau farmecul.'}],
  'link_targets': [{'node_id': 'n_v1_11_lipici',
                    'label': 'Lipici',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'is_a',
                    'claim_to_verify': 'este o substanță adezivă',
                    'direction': 'incoming',
                    'edge_src': 'n_v1_11_lipici',
                    'edge_dst': 'n_v1_19_adeziv',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://dexonline.ro/definitie/lipici/json'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v1_3_material_lemn',
                    'label': 'Lemn',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'există adezivi pentru lipirea lemnului',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_adeziv',
                    'edge_dst': 'n_v1_3_material_lemn',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://catalog.temad.ro/adeziv-bicomponent-rapid-bison-epoxy-5-minute-4ml'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v1_11_sticla',
                    'label': 'Sticlă',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'există adezivi pentru lipirea sticlei',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_adeziv',
                    'edge_dst': 'n_v1_11_sticla',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://catalog.temad.ro/adeziv-bicomponent-rapid-bison-epoxy-5-minute-4ml'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v1_11_cauciuc',
                    'label': 'Cauciuc',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'există adezivi pentru lipirea cauciucului',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_adeziv',
                    'edge_dst': 'n_v1_11_cauciuc',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://catalog.temad.ro/adeziv-bicomponent-rapid-bison-epoxy-5-minute-4ml'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'}],
  'source_acquisition_note': 'TEMAD product page fetched directly;superseded catalogue PDF '
                             'returned404 and contributes no claim;technical directions,numerics '
                             'and safety advice excluded.',
  'current_graph_counts': {'distinct': 5, 'old_main': 4, 'same_category': 5, 'batch': 1},
  'frequency': {'url': 'https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/ro/ro_50k.txt',
                'best_rank': 36050,
                'matched_form': 'adeziv',
                'role': 'Positive signal only; absence does not reject concrete everyday/school '
                        'vocabulary.'},
  'scope': 'Accepted after both once-only independent whole-batch web reviews and explicit verdict '
           'application;reviewed/unapplied/not_landed. No game round,target,recipe,route or '
           'runtime qualification.',
  'review_verdicts': {'factual': {'verdict': 'accept',
                                  'rationale': 'Este substantivul masculin pentru substanța de '
                                               'lipire; se folosește tabelul DOR M1, nu tabelul '
                                               'adjectival.'},
                      'quality': {'verdict': 'accept',
                                  'rationale': 'An everyday household and school material; the '
                                               'masculine noun adezivi is separated from adjective '
                                               'adezive.'}}},
 {'id': 'v119-banda_adeziva',
  'lemma': 'Bandă adezivă',
  'kind': 'new_shared_concept',
  'node_id': 'n_v1_19_banda_adeziva',
  'games': ['Cald sau Rece', 'Lanțul Cuvintelor', 'Conexiuni', 'Intrusul', 'Alchimie'],
  'sense': 'Fâșie prevăzută cu adeziv pentru fixare sau ambalare; sintagma întreagă,nu grupul de '
           'persoane sau forma bande.',
  'register': 'Selected everyday workshop/craft noun sense; unrelated,archaic/poetic-only meanings '
              'excluded;no instructions or clinical ruling.',
  'verified_forms': ['bandă adezivă',
                     'benzi adezive',
                     'benzile adezive',
                     'benzii adezive',
                     'benzilor adezive'],
  'proposed_forms': ['bandă adezivă',
                     'benzi adezive',
                     'benzile adezive',
                     'benzii adezive',
                     'benzilor adezive'],
  'already_resolved_forms': [],
  'already_reserved_forms': [],
  'excluded_form_hypotheses': [],
  'dictionaries': [{'lemma': 'bandă',
                    'url': 'https://dexonline.ro/definitie/band%C4%83/json',
                    'dex_definition_ids': ['832875'],
                    'doom3_definition_ids': ['1317217'],
                    'flexion_url': 'https://dexonline.ro/definitie/band%C4%83',
                    'flexion_authority': 'DOOM3 table explicitly labelled bandă '
                                         '(fâșie),benzi/benzii/benzilor',
                    'forms_note': 'All five pre-screened qualified normalized keys;adjective '
                                  'agreement feminine sg adezivă/pl and gen adezive matches exact '
                                  'DOOM3 Adeziv adjective1321004 observed this tick;bare Bandă is '
                                  'not proposed.',
                    'paraphrase': 'Fâșie prevăzută cu adeziv pentru fixare sau ambalare; sintagma '
                                  'întreagă,nu grupul de persoane sau forma bande.; selected DEX '
                                  'sense/register and DOOM3 lexical gender/number checked, '
                                  'ordinary forms from DOOM3 table explicitly labelled bandă '
                                  '(fâșie),benzi/benzii/benzilor.'}],
  'sources': [{'url': 'https://dexonline.ro/definitie/band%C4%83/json',
               'paraphrase': 'Fâșie prevăzută cu adeziv pentru fixare sau ambalare; sintagma '
                             'întreagă,nu grupul de persoane sau forma bande.; selected DEX '
                             'sense/register and DOOM3 lexical gender/number checked, ordinary '
                             'forms from DOOM3 table explicitly labelled bandă '
                             '(fâșie),benzi/benzii/benzilor.'},
              {'url': 'https://ro.wiktionary.org/wiki/band%C4%83',
               'paraphrase': 'Sensul fâșie are benzi/benzii/benzilor,distinct de grupul cu plural '
                             'bande.'},
              {'url': 'https://www.tesa.com/ro-ro/consumer/tesafilm-paper.html',
               'paraphrase': 'Există bandă adezivă cu suport din hârtie;legătura nu afirmă că '
                             'toate benzile sunt din hârtie.'},
              {'url': 'https://www.tesa.com/ro-ro/consumer/birou-si-office/benzi-pentru-ambalare',
               'paraphrase': 'Benzile de ambalare pot sigila cutii de mutare.'},
              {'url': 'https://www.tesa.com/ro-ro/consumer/solutii-inteligente-montare-agatare-sms/benzi-hook-loop',
               'paraphrase': 'Exemplul Ultra Power Lock poate fi tăiat cu foarfeca;nu se atribuie '
                             'tuturor benzilor aceeași rezistență.'},
              {'url': 'https://www.tesa.com/ro-ro/industrie/tesa-professional-60950.html',
               'paraphrase': 'Exemplul producătorului descrie explicit un strat de adeziv pe '
                             'suportul benzii.'}],
  'link_targets': [{'node_id': 'n_v1_19_adeziv',
                    'label': 'Adeziv',
                    'category': 'viata_de_roman',
                    'status': 'batch',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'are un strat de adeziv',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_banda_adeziva',
                    'edge_dst': 'n_v1_19_adeziv',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://www.tesa.com/ro-ro/industrie/tesa-professional-60950.html'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v1_11_hartie',
                    'label': 'Hârtie',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'poate avea suport din hârtie',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_banda_adeziva',
                    'edge_dst': 'n_v1_11_hartie',
                    'verdict': 'accepted_reviewed_unapplied',
                    'original_claim_hypothesis': 'poate lipi foi de hârtie',
                    'sources': ['https://www.tesa.com/ro-ro/consumer/tesafilm-paper.html'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v1_11_cutie',
                    'label': 'Cutie',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'poate închide o cutie pentru ambalare',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_banda_adeziva',
                    'edge_dst': 'n_v1_11_cutie',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://www.tesa.com/ro-ro/consumer/birou-si-office/benzi-pentru-ambalare'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v1_11_foarfeca',
                    'label': 'Foarfecă',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'poate fi tăiată cu foarfeca',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_banda_adeziva',
                    'edge_dst': 'n_v1_11_foarfeca',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://www.tesa.com/ro-ro/consumer/solutii-inteligente-montare-agatare-sms/benzi-hook-loop'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'}],
  'source_acquisition_note': 'All four manufacturer pages fetched directly;paper caption narrowed '
                             'to explicit support material instead of inferring a paper-gluing '
                             'use. No quantified,certification,safety or instructional claims '
                             'adopted.',
  'qualified_form_note': 'Every proposed form retains adezivă/adezive qualification;bare '
                         'dictionary heads are evidence only.',
  'current_graph_counts': {'distinct': 4, 'old_main': 3, 'same_category': 4, 'batch': 1},
  'frequency': {'url': 'https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/ro/ro_50k.txt',
                'best_rank': None,
                'matched_form': None,
                'role': 'Positive signal only; absence does not reject concrete everyday/school '
                        'vocabulary.'},
  'scope': 'Accepted after both once-only independent whole-batch web reviews and explicit verdict '
           'application;reviewed/unapplied/not_landed. No game round,target,recipe,route or '
           'runtime qualification.',
  'review_verdicts': {'factual': {'verdict': 'accept',
                                  'rationale': 'Sintagma calificată denumește fâșia cu adeziv; '
                                               'benzi/benzii se acordă cu adezive, fără a admite '
                                               'omonimul bande.'},
                      'quality': {'verdict': 'accept',
                                  'rationale': 'A familiar school/packaging object; the whole '
                                               'qualified phrase preserves the fâșie benzi '
                                               'paradigm and feminine adjective agreement.'}}},
 {'id': 'v119-teava',
  'lemma': 'Țeavă',
  'kind': 'new_shared_concept',
  'node_id': 'n_v1_19_teava',
  'games': ['Cald sau Rece', 'Lanțul Cuvintelor', 'Conexiuni', 'Intrusul'],
  'sense': 'Piesă tubulară folosită în instalații; sensul general de tub,nu țeava unei arme sau '
           'suportul textil.',
  'register': 'Selected everyday workshop/craft noun sense; unrelated,archaic/poetic-only meanings '
              'excluded;no instructions or clinical ruling.',
  'verified_forms': ['țeavă', 'țevi', 'țevile', 'țevii', 'țevilor'],
  'proposed_forms': ['țeavă', 'țevi', 'țevile', 'țevii', 'țevilor'],
  'already_resolved_forms': [],
  'already_reserved_forms': [],
  'excluded_form_hypotheses': [{'form': 'țevei',
                                'reason': 'Formă din paradigma veche -e,nu DOOM3 actual '
                                          'țevi/țevii.'}],
  'dictionaries': [{'lemma': 'țeavă',
                    'url': 'https://dexonline.ro/definitie/%C8%9Beav%C4%83/json',
                    'dex_definition_ids': ['829558'],
                    'doom3_definition_ids': ['1265274'],
                    'flexion_url': 'https://dexonline.ro/definitie/%C8%9Beav%C4%83',
                    'flexion_authority': 'DOOM3 first noun table,țevi/țevii/țevilor',
                    'forms_note': 'Five ordinary normalized keys;older DLRLC -e and regional forms '
                                  'excluded.',
                    'paraphrase': 'Piesă tubulară folosită în instalații; sensul general de tub,nu '
                                  'țeava unei arme sau suportul textil.; selected DEX '
                                  'sense/register and DOOM3 lexical gender/number checked, '
                                  'ordinary forms from DOOM3 first noun '
                                  'table,țevi/țevii/țevilor.'}],
  'sources': [{'url': 'https://dexonline.ro/definitie/%C8%9Beav%C4%83/json',
               'paraphrase': 'Piesă tubulară folosită în instalații; sensul general de tub,nu '
                             'țeava unei arme sau suportul textil.; selected DEX sense/register '
                             'and DOOM3 lexical gender/number checked, ordinary forms from DOOM3 '
                             'first noun table,țevi/țevii/țevilor.'},
              {'url': 'https://ro.wiktionary.org/wiki/%C8%9Beav%C4%83',
               'paraphrase': 'Numele piesei tubulare și paradigma țevi/țevii/țevilor corespund '
                             'sensului selectat.'},
              {'url': 'https://www.valrom.ro/wp-content/uploads/2023/08/Aviz-agrement-Piese-trecere-si-bride-Aquer.pdf',
               'paraphrase': 'Pasajul tehnic indexat al producătorului descrie piese care asigură '
                             'trecerea țevilor de canalizare prin pereți.'},
              {'url': 'https://www.knipex.com/ro-ro/produse/cle%C8%99ti-pentru-%C8%9Bevi-%C8%99i-pompe-de-ap%C4%83/knipex-alligator-cleste-pentru-instalatori/knipex-alligator-cleste-pentru-instalatori/8801300?sku=8807250&v=9438',
               'paraphrase': 'Producătorul descrie explicit cleștele cu prindere pe țevi.'},
              {'url': 'https://dexonline.ro/definitie/robinet/json',
               'paraphrase': 'DEX858876:robinetul se montează la capătul sau între conducte;este '
                             'susținută legătura tubului cu robinetul.'},
              {'url': 'https://ro.rothenberger.com/ro-ro/produse/cleste-pentru-pompa-de-apa/set-de-clesti-cleste-pentru-tevi-1-1-1-2-cleste-tip-papagal-sp-10-070140x/',
               'paraphrase': 'Pagina proprie a producătorului confirmă prinderea țevilor cu '
                             'această clasă de clești;izvor proaspăt verificat independent.'}],
  'link_targets': [{'node_id': 'n_v4sti_metal',
                    'label': 'metal',
                    'category': 'stiinta',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'poate fi fabricată din metal',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_teava',
                    'edge_dst': 'n_v4sti_metal',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://dexonline.ro/definitie/%C8%9Beav%C4%83/json'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v33_bathroom_fixture_robinet',
                    'label': 'Robinet',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'poate fi legată la un robinet',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_teava',
                    'edge_dst': 'n_v33_bathroom_fixture_robinet',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://dexonline.ro/definitie/robinet/json'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v24_home_structure_perete',
                    'label': 'Perete',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'poate traversa un perete într-o instalație',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_teava',
                    'edge_dst': 'n_v24_home_structure_perete',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://www.valrom.ro/wp-content/uploads/2023/08/Aviz-agrement-Piese-trecere-si-bride-Aquer.pdf'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v32_workshop_hand_cleste',
                    'label': 'Clește',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'poate fi prinsă cu un clește pentru țevi',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_teava',
                    'edge_dst': 'n_v32_workshop_hand_cleste',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://ro.rothenberger.com/ro-ro/produse/cleste-pentru-pompa-de-apa/set-de-clesti-cleste-pentru-tevi-1-1-1-2-cleste-tip-papagal-sp-10-070140x/'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'}],
  'source_acquisition_note': 'VALROM PDF fetched directly but scanned text extraction empty;only '
                             'the exact primary indexed passage,not a full-text read,binds the '
                             'wall claim. KNIPEX direct request403;web reader opened full page and '
                             'its pipe-gripping bullet. No approvals,regulations,dimensions,safety '
                             'or installation directions adopted.',
  'current_graph_counts': {'distinct': 5, 'old_main': 4, 'same_category': 3, 'batch': 1},
  'frequency': {'url': 'https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/ro/ro_50k.txt',
                'best_rank': 13512,
                'matched_form': 'țeavă',
                'role': 'Positive signal only; absence does not reject concrete everyday/school '
                        'vocabulary.'},
  'scope': 'Accepted after both once-only independent whole-batch web reviews and explicit verdict '
           'application;reviewed/unapplied/not_landed. No game round,target,recipe,route or '
           'runtime qualification.',
  'review_corrections': [{'kind': 'replace_edge_source_binding',
                          'src': 'n_v1_19_teava',
                          'dst': 'n_v32_workshop_hand_cleste',
                          'relation': 'related_to',
                          'before': ['https://www.knipex.com/ro-ro/produse/cle%C8%99ti-pentru-%C8%9Bevi-%C8%99i-pompe-de-ap%C4%83/knipex-alligator-cleste-pentru-instalatori/knipex-alligator-cleste-pentru-instalatori/8801300?sku=8807250&v=9438'],
                          'after': ['https://ro.rothenberger.com/ro-ro/produse/cleste-pentru-pompa-de-apa/set-de-clesti-cleste-pentru-tevi-1-1-1-2-cleste-tip-papagal-sp-10-070140x/'],
                          'reviewers': ['quality']}],
  'fresh_review_source_binding_notes': ['The exact correction above supplies the current reviewed '
                                        'edge authority; earlier acquisition notes describe '
                                        'historical author research and do not override the fresh '
                                        'binding.'],
  'review_verdicts': {'factual': {'verdict': 'accept',
                                  'rationale': 'Este tubul pentru instalații; paradigma țevi/țevii '
                                               'este confirmată, fără sensul de armă sau suport '
                                               'textil.'},
                      'quality': {'verdict': 'modify',
                                  'rationale': 'A familiar household installation pipe; the '
                                               'scanned wall-pass evidence is visually verified '
                                               'and the tongs source binding must be replaced.'}}},
 {'id': 'v119-tigla',
  'lemma': 'Țiglă',
  'kind': 'new_shared_concept',
  'node_id': 'n_v1_19_tigla',
  'games': ['Cald sau Rece', 'Lanțul Cuvintelor', 'Conexiuni', 'Intrusul'],
  'sense': 'Placă folosită la învelirea acoperișurilor,în special din argilă arsă;nu sensul '
           'regional frigare.',
  'register': 'Selected everyday workshop/craft noun sense; unrelated,archaic/poetic-only meanings '
              'excluded;no instructions or clinical ruling.',
  'verified_forms': ['țiglă', 'țigle', 'țiglele', 'țiglei', 'țiglelor'],
  'proposed_forms': ['țiglă', 'țigle', 'țiglele', 'țiglei', 'țiglelor'],
  'already_resolved_forms': [],
  'already_reserved_forms': [],
  'excluded_form_hypotheses': [],
  'dictionaries': [{'lemma': 'țiglă',
                    'url': 'https://dexonline.ro/definitie/%C8%9Bigl%C4%83/json',
                    'dex_definition_ids': ['829770'],
                    'doom3_definition_ids': ['1265342'],
                    'flexion_url': 'https://dexonline.ro/definitie/%C8%9Bigl%C4%83',
                    'flexion_authority': 'DOOM3 table explicitly labelled țiglă (placă)',
                    'forms_note': 'Five ordinary normalized keys,țigle/țiglei/țiglelor;regional '
                                  'skewer and variants excluded.',
                    'paraphrase': 'Placă folosită la învelirea acoperișurilor,în special din '
                                  'argilă arsă;nu sensul regional frigare.; selected DEX '
                                  'sense/register and DOOM3 lexical gender/number checked, '
                                  'ordinary forms from DOOM3 table explicitly labelled țiglă '
                                  '(placă).'}],
  'sources': [{'url': 'https://dexonline.ro/definitie/%C8%9Bigl%C4%83/json',
               'paraphrase': 'Placă folosită la învelirea acoperișurilor,în special din argilă '
                             'arsă;nu sensul regional frigare.; selected DEX sense/register and '
                             'DOOM3 lexical gender/number checked, ordinary forms from DOOM3 table '
                             'explicitly labelled țiglă (placă).'},
              {'url': 'https://ro.wiktionary.org/wiki/%C8%9Bigl%C4%83',
               'paraphrase': 'Sensul de placă pentru învelirea caselor și paradigma țigle/țiglei '
                             'sunt distincte de frigare.'},
              {'url': 'https://www.wienerberger.ro/content/dam/wienerberger/romania/marketing/documents-magazines/brochures/Instructiuni%20de%20montaj%20tigla%20cu%20falt%20lateral%20si%20superior.pdf',
               'paraphrase': 'Manualul producătorului descrie acoperișul ceramic pe șipci din lemn '
                             'și fixarea țiglelor cu șuruburi,sârmă,cleme ori cuie.'},
              {'url': 'https://dexonline.ro/definitie/cui/json',
               'paraphrase': 'Definiția cuiului confirmă materialul metalic al unui accesoriu '
                             'numit explicit la fixarea țiglelor.'}],
  'link_targets': [{'node_id': 'n_v24_home_structure_acoperis',
                    'label': 'Acoperiș',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'part_of',
                    'claim_to_verify': 'poate face parte din învelitoarea acoperișului',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_tigla',
                    'edge_dst': 'n_v24_home_structure_acoperis',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://www.wienerberger.ro/content/dam/wienerberger/romania/marketing/documents-magazines/brochures/Instructiuni%20de%20montaj%20tigla%20cu%20falt%20lateral%20si%20superior.pdf'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v4soc_casa',
                    'label': 'casă',
                    'category': 'societate',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'poate acoperi o casă',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_tigla',
                    'edge_dst': 'n_v4soc_casa',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://dexonline.ro/definitie/%C8%9Bigl%C4%83/json'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v1_3_material_lemn',
                    'label': 'Lemn',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'poate fi fixată pe șipci de lemn ale acoperișului',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_tigla',
                    'edge_dst': 'n_v1_3_material_lemn',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://www.wienerberger.ro/content/dam/wienerberger/romania/marketing/documents-magazines/brochures/Instructiuni%20de%20montaj%20tigla%20cu%20falt%20lateral%20si%20superior.pdf'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v4sti_metal',
                    'label': 'metal',
                    'category': 'stiinta',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'poate fi fixată cu accesorii metalice',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_tigla',
                    'edge_dst': 'n_v4sti_metal',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://www.wienerberger.ro/content/dam/wienerberger/romania/marketing/documents-magazines/brochures/Instructiuni%20de%20montaj%20tigla%20cu%20falt%20lateral%20si%20superior.pdf',
                                'https://dexonline.ro/definitie/cui/json'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'}],
  'source_acquisition_note': 'Roof manual fetched directly and text extracted in memory;no raw PDF '
                             'retained. Metal caption is a stated inference from the manual’s '
                             'explicit nails plus DEX metal-nail definition. No '
                             'numeric,structural,safety or mounting instructions adopted.',
  'current_graph_counts': {'distinct': 4, 'old_main': 4, 'same_category': 2, 'batch': 0},
  'frequency': {'url': 'https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/ro/ro_50k.txt',
                'best_rank': 49829,
                'matched_form': 'țiglă',
                'role': 'Positive signal only; absence does not reject concrete everyday/school '
                        'vocabulary.'},
  'scope': 'Accepted after both once-only independent whole-batch web reviews and explicit verdict '
           'application;reviewed/unapplied/not_landed. No game round,target,recipe,route or '
           'runtime qualification.',
  'review_verdicts': {'factual': {'verdict': 'accept',
                                  'rationale': 'Este placa pentru acoperiș, distinctă de frigarea '
                                               'regională; paradigma țigle este confirmată.'},
                      'quality': {'verdict': 'accept',
                                  'rationale': 'Ordinary roof vocabulary supported by Romanian '
                                               'school materials and a roof-system producer; the '
                                               'regional spit sense is excluded.'}}},
 {'id': 'v119-caramida',
  'lemma': 'Cărămidă',
  'kind': 'new_shared_concept',
  'node_id': 'n_v1_19_caramida',
  'games': ['Cald sau Rece', 'Lanțul Cuvintelor', 'Conexiuni', 'Intrusul'],
  'sense': 'Piesă de construcție obținută din argilă sau alte materiale,uscată ori arsă;nu '
           'sensurile argotice.',
  'register': 'Selected everyday workshop/craft noun sense; unrelated,archaic/poetic-only meanings '
              'excluded;no instructions or clinical ruling.',
  'verified_forms': ['cărămidă', 'cărămizi', 'cărămizile', 'cărămizii', 'cărămizilor'],
  'proposed_forms': ['cărămidă', 'cărămizi', 'cărămizile', 'cărămizii', 'cărămizilor'],
  'already_resolved_forms': [],
  'already_reserved_forms': [],
  'excluded_form_hypotheses': [],
  'dictionaries': [{'lemma': 'cărămidă',
                    'url': 'https://dexonline.ro/definitie/c%C4%83r%C4%83mid%C4%83/json',
                    'dex_definition_ids': ['843102'],
                    'doom3_definition_ids': ['1310446'],
                    'flexion_url': 'https://dexonline.ro/definitie/c%C4%83r%C4%83mid%C4%83',
                    'flexion_authority': 'DOR first feminine noun table agreeing with DOOM3 '
                                         'cărămizi/cărămizii',
                    'forms_note': 'Five ordinary normalized keys;alternate old -e paradigm and '
                                  'regional forms not admitted.',
                    'paraphrase': 'Piesă de construcție obținută din argilă sau alte '
                                  'materiale,uscată ori arsă;nu sensurile argotice.; selected DEX '
                                  'sense/register and DOOM3 lexical gender/number checked, '
                                  'ordinary forms from DOR first feminine noun table agreeing with '
                                  'DOOM3 cărămizi/cărămizii.'}],
  'sources': [{'url': 'https://dexonline.ro/definitie/c%C4%83r%C4%83mid%C4%83/json',
               'paraphrase': 'Piesă de construcție obținută din argilă sau alte materiale,uscată '
                             'ori arsă;nu sensurile argotice.; selected DEX sense/register and '
                             'DOOM3 lexical gender/number checked, ordinary forms from DOR first '
                             'feminine noun table agreeing with DOOM3 cărămizi/cărămizii.'},
              {'url': 'https://ro.wiktionary.org/wiki/c%C4%83r%C4%83mid%C4%83',
               'paraphrase': 'Paradigma cărămizi/cărămizii/cărămizilor și sensul de material de '
                             'construcție sunt distincte de argou.'},
              {'url': 'https://www.wienerberger.ro/pentru-profesionisti/arhitecti/brick-award/inscrieri-brick-award-22/proiecte-inscrise-in-romania/rezidential-unifamilial.html',
               'paraphrase': 'Exemplele proprii ale producătorului arată case și pereți din '
                             'cărămidă și clasifică produsele în materiale ceramice.'},
              {'url': 'https://www.kaiserkraft.ro/dispozitive-de-transport-si-carucioare/roabe/c/1082790-KK/',
               'paraphrase': 'Categoria vânzătorului include explicit roabe pentru piatră și '
                             'cărămizi.'},
              {'url': 'https://ro.wikipedia.org/wiki/C%C4%83r%C4%83mid%C4%83',
               'paraphrase': 'Cărămizile sunt folosite la ziduri și pot fi arse în cuptor;nu sunt '
                             'adoptate cronologia sau aprecierile comerciale.'}],
  'link_targets': [{'node_id': 'n_v24_home_structure_perete',
                    'label': 'Perete',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'part_of',
                    'claim_to_verify': 'poate intra în alcătuirea unui perete',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_caramida',
                    'edge_dst': 'n_v24_home_structure_perete',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://www.wienerberger.ro/pentru-profesionisti/arhitecti/brick-award/inscrieri-brick-award-22/proiecte-inscrise-in-romania/rezidential-unifamilial.html',
                                'https://ro.wikipedia.org/wiki/C%C4%83r%C4%83mid%C4%83'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v4soc_casa',
                    'label': 'casă',
                    'category': 'societate',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'poate fi folosită la construirea unei case',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_caramida',
                    'edge_dst': 'n_v4soc_casa',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://www.wienerberger.ro/pentru-profesionisti/arhitecti/brick-award/inscrieri-brick-award-22/proiecte-inscrise-in-romania/rezidential-unifamilial.html',
                                'https://ro.wikipedia.org/wiki/C%C4%83r%C4%83mid%C4%83'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v32_garden_transport_roaba',
                    'label': 'Roabă',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'poate fi transportată cu roaba',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_caramida',
                    'edge_dst': 'n_v32_garden_transport_roaba',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://www.kaiserkraft.ro/dispozitive-de-transport-si-carucioare/roabe/c/1082790-KK/'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v4art_ceramica',
                    'label': 'Ceramică',
                    'category': 'arta_cultura',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'cărămida arsă este un produs ceramic',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_caramida',
                    'edge_dst': 'n_v4art_ceramica',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://www.wienerberger.ro/pentru-profesionisti/arhitecti/brick-award/inscrieri-brick-award-22/proiecte-inscrise-in-romania/rezidential-unifamilial.html',
                                'https://ro.wikipedia.org/wiki/C%C4%83r%C4%83mid%C4%83'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'}],
  'source_acquisition_note': 'Manufacturer house page,seller wheelbarrow page and Romanian article '
                             'fetched directly. Catalogue404 supplies no evidence. No named '
                             'architects,places,dates,dimensions,performance or instructions '
                             'adopted.',
  'current_graph_counts': {'distinct': 4, 'old_main': 4, 'same_category': 2, 'batch': 0},
  'frequency': {'url': 'https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/ro/ro_50k.txt',
                'best_rank': 12777,
                'matched_form': 'cărămidă',
                'role': 'Positive signal only; absence does not reject concrete everyday/school '
                        'vocabulary.'},
  'scope': 'Accepted after both once-only independent whole-batch web reviews and explicit verdict '
           'application;reviewed/unapplied/not_landed. No game round,target,recipe,route or '
           'runtime qualification.',
  'review_verdicts': {'factual': {'verdict': 'accept',
                                  'rationale': 'Este piesa de zidărie, inclusiv produsul ceramic '
                                               'ars; familia cărămizi/cărămizii este normativă.'},
                      'quality': {'verdict': 'accept',
                                  'rationale': 'A common school and house-building noun; the '
                                               'ordinary masonry piece, not slang uses, has the '
                                               'full cărămizi family.'}}},
 {'id': 'v119-mortar',
  'lemma': 'Mortar',
  'kind': 'new_shared_concept',
  'node_id': 'n_v1_19_mortar',
  'games': ['Cald sau Rece', 'Lanțul Cuvintelor', 'Conexiuni', 'Intrusul', 'Alchimie'],
  'sense': 'Amestec de construcție care leagă piese solide,precum cărămizile;nu termen străin '
           'pentru armă.',
  'register': 'Selected everyday workshop/craft noun sense; unrelated,archaic/poetic-only meanings '
              'excluded;no instructions or clinical ruling.',
  'verified_forms': ['mortar', 'mortarul', 'mortare', 'mortarele', 'mortarului', 'mortarelor'],
  'proposed_forms': ['mortar', 'mortarul', 'mortare', 'mortarele', 'mortarului', 'mortarelor'],
  'already_resolved_forms': [],
  'already_reserved_forms': [],
  'excluded_form_hypotheses': [],
  'dictionaries': [{'lemma': 'mortar',
                    'url': 'https://dexonline.ro/definitie/mortar/json',
                    'dex_definition_ids': ['892016'],
                    'doom3_definition_ids': ['1294689'],
                    'flexion_url': 'https://dexonline.ro/definitie/mortar',
                    'flexion_authority': 'DOR neuter mortar table agreeing with DOOM3 mortare',
                    'forms_note': 'Six ordinary normalized keys;elisions excluded.',
                    'paraphrase': 'Amestec de construcție care leagă piese solide,precum '
                                  'cărămizile;nu termen străin pentru armă.; selected DEX '
                                  'sense/register and DOOM3 lexical gender/number checked, '
                                  'ordinary forms from DOR neuter mortar table agreeing with DOOM3 '
                                  'mortare.'}],
  'sources': [{'url': 'https://dexonline.ro/definitie/mortar/json',
               'paraphrase': 'Amestec de construcție care leagă piese solide,precum cărămizile;nu '
                             'termen străin pentru armă.; selected DEX sense/register and DOOM3 '
                             'lexical gender/number checked, ordinary forms from DOR neuter mortar '
                             'table agreeing with DOOM3 mortare.'},
              {'url': 'https://ro.wiktionary.org/wiki/mortar',
               'paraphrase': 'Substantiv neutru mortare/mortarului/mortarelor pentru amestecul '
                             'care leagă cărămizi ori tencuiește.'},
              {'url': 'https://www.cemix.ro/ro/p/1300-Mortare-de-zidarie/1310-MM-10',
               'paraphrase': 'Mortarul de zidărie al producătorului folosește ciment și permite '
                             'prepararea cu apă potabilă;nu se adoptă rețeta sau standardul.'}],
  'link_targets': [{'node_id': 'n_v1_19_ciment',
                    'label': 'Ciment',
                    'category': 'viata_de_roman',
                    'status': 'batch',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'poate conține ciment drept liant',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_mortar',
                    'edge_dst': 'n_v1_19_ciment',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://dexonline.ro/definitie/mortar/json',
                                'https://www.cemix.ro/ro/p/1300-Mortare-de-zidarie/1310-MM-10'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v4geo_nisip',
                    'label': 'nisip',
                    'category': 'geografie',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'poate conține nisip',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_mortar',
                    'edge_dst': 'n_v4geo_nisip',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://dexonline.ro/definitie/mortar/json',
                                'https://ro.wiktionary.org/wiki/mortar'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v4gas_apa',
                    'label': 'Apă',
                    'category': 'gastronomie',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'poate fi preparat cu apă potabilă',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_mortar',
                    'edge_dst': 'n_v4gas_apa',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://www.cemix.ro/ro/p/1300-Mortare-de-zidarie/1310-MM-10'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v24_home_structure_perete',
                    'label': 'Perete',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'poate lega elementele unui perete',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_mortar',
                    'edge_dst': 'n_v24_home_structure_perete',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://dexonline.ro/definitie/mortar/json',
                                'https://ro.wiktionary.org/wiki/mortar'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'}],
  'source_acquisition_note': 'CEMIX page fetched directly. Potable-water claim deliberately '
                             'matches the served Apă sense. No mixing '
                             'amounts,standards,performance or construction advice adopted.',
  'current_graph_counts': {'distinct': 5, 'old_main': 3, 'same_category': 3, 'batch': 2},
  'frequency': {'url': 'https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/ro/ro_50k.txt',
                'best_rank': 40191,
                'matched_form': 'mortar',
                'role': 'Positive signal only; absence does not reject concrete everyday/school '
                        'vocabulary.'},
  'scope': 'Accepted after both once-only independent whole-batch web reviews and explicit verdict '
           'application;reviewed/unapplied/not_landed. No game round,target,recipe,route or '
           'runtime qualification.',
  'review_verdicts': {'factual': {'verdict': 'accept',
                                  'rationale': 'Este amestecul liant pentru zidărie; familia '
                                               'mortare și legăturile către ciment, nisip și apă '
                                               'potabilă sunt confirmate.'},
                      'quality': {'verdict': 'accept',
                                  'rationale': 'An ordinary construction material in school '
                                               'chemistry and current masonry products; the '
                                               'drinking-water endpoint is explicitly supported by '
                                               'potable-water wording.'}}},
 {'id': 'v119-ciment',
  'lemma': 'Ciment',
  'kind': 'new_shared_concept',
  'node_id': 'n_v1_19_ciment',
  'games': ['Cald sau Rece', 'Lanțul Cuvintelor', 'Conexiuni', 'Intrusul'],
  'sense': 'Pulbere folosită ca liant în construcții;pluralul cimenturi denumește '
           'sortimente,nicidecum betonul ca sinonim.',
  'register': 'Selected everyday workshop/craft noun sense; unrelated,archaic/poetic-only meanings '
              'excluded;no instructions or clinical ruling.',
  'verified_forms': ['ciment',
                     'cimentul',
                     'cimenturi',
                     'cimenturile',
                     'cimentului',
                     'cimenturilor'],
  'proposed_forms': ['ciment',
                     'cimentul',
                     'cimenturi',
                     'cimenturile',
                     'cimentului',
                     'cimenturilor'],
  'already_resolved_forms': [],
  'already_reserved_forms': [],
  'excluded_form_hypotheses': [],
  'dictionaries': [{'lemma': 'ciment',
                    'url': 'https://dexonline.ro/definitie/ciment/json',
                    'dex_definition_ids': ['846023'],
                    'doom3_definition_ids': ['1311637'],
                    'flexion_url': 'https://dexonline.ro/definitie/ciment',
                    'flexion_authority': 'DOOM3 ciment (material de construcție) table,plural '
                                         'cimenturi (sorturi)',
                    'forms_note': 'Six ordinary normalized keys;plural explicitly sortal per '
                                  'DEX/DOOM3,not individual powder units;vocative and elisions '
                                  'excluded.',
                    'paraphrase': 'Pulbere folosită ca liant în construcții;pluralul cimenturi '
                                  'denumește sortimente,nicidecum betonul ca sinonim.; selected '
                                  'DEX sense/register and DOOM3 lexical gender/number checked, '
                                  'ordinary forms from DOOM3 ciment (material de construcție) '
                                  'table,plural cimenturi (sorturi).'}],
  'sources': [{'url': 'https://dexonline.ro/definitie/ciment/json',
               'paraphrase': 'Pulbere folosită ca liant în construcții;pluralul cimenturi '
                             'denumește sortimente,nicidecum betonul ca sinonim.; selected DEX '
                             'sense/register and DOOM3 lexical gender/number checked, ordinary '
                             'forms from DOOM3 ciment (material de construcție) table,plural '
                             'cimenturi (sorturi).'},
              {'url': 'https://ro.wiktionary.org/wiki/ciment',
               'paraphrase': 'Ciment/cimenturi este substantiv neutru;formele de caz corespund '
                             'tabelului normativ.'},
              {'url': 'https://www.holcim.ro/sites/romania/files/2022-09/holcim_sd_report_2009-2010-1.pdf',
               'paraphrase': 'Glosarul producătorului explică cimentul ca liant pentru beton și '
                             'mortar și arată calcarul ca adaos mineral.'},
              {'url': 'https://www.holcim.ro/ro/extradur-52-vrac',
               'paraphrase': 'Un ciment al producătorului este destinat inclusiv elementelor din '
                             'beton pentru panouri de perete.'},
              {'url': 'https://www.cemix.ro/ro/p/1300-Mortare-de-zidarie/1310-MM-10',
               'paraphrase': 'Mortarul de zidărie verificat în același tick are ciment gri drept '
                             'liant;pagina este reutilizată,nu refetch pretins.'}],
  'link_targets': [{'node_id': 'n_v1_19_mortar',
                    'label': 'Mortar',
                    'category': 'viata_de_roman',
                    'status': 'batch',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'poate conține ciment drept liant',
                    'direction': 'incoming',
                    'edge_src': 'n_v1_19_mortar',
                    'edge_dst': 'n_v1_19_ciment',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://www.cemix.ro/ro/p/1300-Mortare-de-zidarie/1310-MM-10',
                                'https://www.holcim.ro/sites/romania/files/2022-09/holcim_sd_report_2009-2010-1.pdf'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v1_19_beton',
                    'label': 'Beton',
                    'category': 'viata_de_roman',
                    'status': 'batch',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'betonul de ciment folosește ciment ca liant',
                    'direction': 'incoming',
                    'edge_src': 'n_v1_19_beton',
                    'edge_dst': 'n_v1_19_ciment',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://www.holcim.ro/sites/romania/files/2022-09/holcim_sd_report_2009-2010-1.pdf'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v28_nature_material_piatra',
                    'label': 'Piatră',
                    'category': 'stiinta',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'materiile sale prime pot include rocă de calcar',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_ciment',
                    'edge_dst': 'n_v28_nature_material_piatra',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://www.holcim.ro/sites/romania/files/2022-09/holcim_sd_report_2009-2010-1.pdf'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v24_home_structure_perete',
                    'label': 'Perete',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'intră în betoane folosite la pereți',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_ciment',
                    'edge_dst': 'n_v24_home_structure_perete',
                    'verdict': 'accepted_reviewed_unapplied',
                    'original_claim_hypothesis': 'intră în mortare și betoane folosite la pereți',
                    'sources': ['https://www.holcim.ro/ro/extradur-52-vrac'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'}],
  'source_acquisition_note': 'Holcim report PDF and wall-product page fetched directly. Historical '
                             'report used only for stable material/binder facts;company '
                             'status,certifications,numbers and engineering directions excluded. '
                             'Missing Heidelberg URL contributes no evidence.',
  'number_scope': 'Sortal plural cimenturi is normative and admitted with the '
                  'construction-material sense.',
  'current_graph_counts': {'distinct': 4, 'old_main': 2, 'same_category': 3, 'batch': 2},
  'frequency': {'url': 'https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/ro/ro_50k.txt',
                'best_rank': 13425,
                'matched_form': 'ciment',
                'role': 'Positive signal only; absence does not reject concrete everyday/school '
                        'vocabulary.'},
  'scope': 'Accepted after both once-only independent whole-batch web reviews and explicit verdict '
           'application;reviewed/unapplied/not_landed. No game round,target,recipe,route or '
           'runtime qualification.',
  'review_verdicts': {'factual': {'verdict': 'accept',
                                  'rationale': 'Sensul de pulbere liantă este confirmat; pluralul '
                                               'cimenturi denumește sorturi ale materialului, nu '
                                               'sinonime noi.'},
                      'quality': {'verdict': 'accept',
                                  'rationale': 'School and current building-product usage support '
                                               'broad familiarity; cimenturi is the normative '
                                               'plural of sorts, not separate countable lumps.'}}},
 {'id': 'v119-beton',
  'lemma': 'Beton',
  'kind': 'new_shared_concept',
  'node_id': 'n_v1_19_beton',
  'games': ['Cald sau Rece', 'Lanțul Cuvintelor', 'Conexiuni', 'Intrusul', 'Alchimie'],
  'sense': 'Material de construcție din liant,apă și agregate;pluralul betoane denumește '
           'sorturi,nu apărarea sportivă sau adjectivul argotic.',
  'register': 'Selected everyday workshop/craft noun sense; unrelated,archaic/poetic-only meanings '
              'excluded;no instructions or clinical ruling.',
  'verified_forms': ['beton', 'betonul', 'betoane', 'betoanele', 'betonului', 'betoanelor'],
  'proposed_forms': ['beton', 'betonul', 'betoane', 'betoanele', 'betonului', 'betoanelor'],
  'already_resolved_forms': [],
  'already_reserved_forms': [],
  'excluded_form_hypotheses': [],
  'dictionaries': [{'lemma': 'beton',
                    'url': 'https://dexonline.ro/definitie/beton/json',
                    'dex_definition_ids': ['834522'],
                    'doom3_definition_ids': ['1318050'],
                    'flexion_url': 'https://dexonline.ro/definitie/beton',
                    'flexion_authority': 'First DOOM3 neuter table,sortal plural betoane',
                    'forms_note': 'Six normalized keys with betoane/betoanelor;Wiktionary/older '
                                  '-uri variant,elisions and vocatives excluded.',
                    'paraphrase': 'Material de construcție din liant,apă și agregate;pluralul '
                                  'betoane denumește sorturi,nu apărarea sportivă sau adjectivul '
                                  'argotic.; selected DEX sense/register and DOOM3 lexical '
                                  'gender/number checked, ordinary forms from First DOOM3 neuter '
                                  'table,sortal plural betoane.'}],
  'sources': [{'url': 'https://dexonline.ro/definitie/beton/json',
               'paraphrase': 'Material de construcție din liant,apă și agregate;pluralul betoane '
                             'denumește sorturi,nu apărarea sportivă sau adjectivul argotic.; '
                             'selected DEX sense/register and DOOM3 lexical gender/number checked, '
                             'ordinary forms from First DOOM3 neuter table,sortal plural betoane.'},
              {'url': 'https://ro.wiktionary.org/wiki/beton',
               'paraphrase': 'Al doilea izvor confirmă sensul de material;pluralul său -uri nu '
                             'este adoptat,DOOM3 cere betoane pentru sorturi.'},
              {'url': 'https://www.holcim.ro/sites/romania/files/2022-09/holcim_sd_report_2009-2010-1.pdf',
               'paraphrase': 'Glosarul producătorului definește betonul prin ciment ca liant și '
                             'agregate precum nisip și pietriș;izvor reutilizat din același tick.'},
              {'url': 'https://www.holcim.ro/ro/extradur-52-vrac',
               'paraphrase': 'Producătorul numește panouri de perete printre elementele din '
                             'beton;pagina deja citită la Ciment,nu refetch pretins.'},
              {'url': 'https://www.triton.com.ro/scule-de-mana/transport-material/roabe',
               'paraphrase': 'Vânzătorul descrie roaba de construcții pentru transportul '
                             'betonului,cărămizilor sau molozului.'}],
  'link_targets': [{'node_id': 'n_v1_19_ciment',
                    'label': 'Ciment',
                    'category': 'viata_de_roman',
                    'status': 'batch',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'betonul de ciment folosește ciment ca liant',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_beton',
                    'edge_dst': 'n_v1_19_ciment',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://dexonline.ro/definitie/beton/json',
                                'https://www.holcim.ro/sites/romania/files/2022-09/holcim_sd_report_2009-2010-1.pdf'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v4geo_nisip',
                    'label': 'nisip',
                    'category': 'geografie',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'poate conține nisip ca agregat fin',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_beton',
                    'edge_dst': 'n_v4geo_nisip',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://dexonline.ro/definitie/beton/json',
                                'https://www.holcim.ro/sites/romania/files/2022-09/holcim_sd_report_2009-2010-1.pdf'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v28_nature_material_piatra',
                    'label': 'Piatră',
                    'category': 'stiinta',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'poate conține piatră ca agregat grosier',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_beton',
                    'edge_dst': 'n_v28_nature_material_piatra',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://dexonline.ro/definitie/beton/json',
                                'https://www.holcim.ro/sites/romania/files/2022-09/holcim_sd_report_2009-2010-1.pdf'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v24_home_structure_perete',
                    'label': 'Perete',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'poate forma pereți',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_beton',
                    'edge_dst': 'n_v24_home_structure_perete',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://www.holcim.ro/ro/extradur-52-vrac'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v32_garden_transport_roaba',
                    'label': 'Roabă',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'betonul proaspăt poate fi transportat cu roaba',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_beton',
                    'edge_dst': 'n_v32_garden_transport_roaba',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://www.triton.com.ro/scule-de-mana/transport-material/roabe'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'}],
  'source_acquisition_note': 'Triton category fetched directly. Holcim documents already read this '
                             'tick are explicitly reused. Piatră caption refers to gravel as '
                             'coarse stone aggregate;no recipe,quantities,transport loads or '
                             'engineering instructions adopted.',
  'number_scope': 'Normative sortal plural betoane;not a count of individual concrete objects.',
  'current_graph_counts': {'distinct': 6, 'old_main': 4, 'same_category': 4, 'batch': 2},
  'frequency': {'url': 'https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/ro/ro_50k.txt',
                'best_rank': 6143,
                'matched_form': 'beton',
                'role': 'Positive signal only; absence does not reject concrete everyday/school '
                        'vocabulary.'},
  'scope': 'Accepted after both once-only independent whole-batch web reviews and explicit verdict '
           'application;reviewed/unapplied/not_landed. No game round,target,recipe,route or '
           'runtime qualification.',
  'review_verdicts': {'factual': {'verdict': 'accept',
                                  'rationale': 'Este materialul cu liant și agregate; pluralul '
                                               'betoane denumește sorturi, cu sensul sportiv '
                                               'exclus.'},
                      'quality': {'verdict': 'accept',
                                  'rationale': 'A familiar building material with school and '
                                               'producer evidence; betoane denotes sorts and the '
                                               'older betonuri table is not admitted.'}}},
 {'id': 'v119-tencuiala',
  'lemma': 'Tencuială',
  'kind': 'new_shared_concept',
  'node_id': 'n_v1_19_tencuiala',
  'games': ['Cald sau Rece', 'Lanțul Cuvintelor', 'Conexiuni', 'Intrusul'],
  'sense': 'Strat de mortar de pe ziduri și tavane;este selectat stratul material,nu acțiunea '
           'tencuirii.',
  'register': 'Selected everyday workshop/craft noun sense; unrelated,archaic/poetic-only meanings '
              'excluded;no instructions or clinical ruling.',
  'verified_forms': ['tencuială', 'tencuieli', 'tencuielile', 'tencuielii', 'tencuielilor'],
  'proposed_forms': ['tencuială', 'tencuieli', 'tencuielile', 'tencuielii', 'tencuielilor'],
  'already_resolved_forms': [],
  'already_reserved_forms': [],
  'excluded_form_hypotheses': [{'form': 'tencuielei',
                                'reason': 'Ipoteză neconformă cu DOOM3 tencuielii.'}],
  'dictionaries': [{'lemma': 'tencuială',
                    'url': 'https://dexonline.ro/definitie/tencuial%C4%83/json',
                    'dex_definition_ids': ['832156'],
                    'doom3_definition_ids': ['1268331'],
                    'flexion_url': 'https://dexonline.ro/definitie/tencuial%C4%83',
                    'flexion_authority': 'DOR feminine table agreeing with DOOM3 '
                                         'tencuielii/tencuieli',
                    'forms_note': 'Five ordinary normalized keys;wrong tencuielei and regional '
                                  'variants excluded.',
                    'paraphrase': 'Strat de mortar de pe ziduri și tavane;este selectat stratul '
                                  'material,nu acțiunea tencuirii.; selected DEX sense/register '
                                  'and DOOM3 lexical gender/number checked, ordinary forms from '
                                  'DOR feminine table agreeing with DOOM3 tencuielii/tencuieli.'}],
  'sources': [{'url': 'https://dexonline.ro/definitie/tencuial%C4%83/json',
               'paraphrase': 'Strat de mortar de pe ziduri și tavane;este selectat stratul '
                             'material,nu acțiunea tencuirii.; selected DEX sense/register and '
                             'DOOM3 lexical gender/number checked, ordinary forms from DOR '
                             'feminine table agreeing with DOOM3 tencuielii/tencuieli.'},
              {'url': 'https://ro.wiktionary.org/wiki/tencuial%C4%83',
               'paraphrase': 'Sensul de strat pe ziduri/tavane și paradigma '
                             'tencuieli/tencuielii/tencuielilor sunt explicite.'},
              {'url': 'https://www.cemix.ro/ro/p/2000-Tencuieli-de-baza/2023-MP-503-A',
               'paraphrase': 'Tencuiala producătorului se aplică și pe beton și poate fi finisată '
                             'cu vopsea;nu se atribuie acestui produs o compoziție de var '
                             'neindicată.'},
              {'url': 'https://my.baumit.ro/produse-tencuieli-decorative-vopsele-%C8%99i-gleturi',
               'paraphrase': 'Catalogul producătorului descrie KlimaDekor ca tencuială decorativă '
                             'pe bază de var;exemplu exact pentru legătura generică unele '
                             'tencuieli folosesc var.'}],
  'link_targets': [{'node_id': 'n_v1_19_beton',
                    'label': 'Beton',
                    'category': 'viata_de_roman',
                    'status': 'batch',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'poate acoperi suprafețe din beton',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_tencuiala',
                    'edge_dst': 'n_v1_19_beton',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://www.cemix.ro/ro/p/2000-Tencuieli-de-baza/2023-MP-503-A'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v1_19_var',
                    'label': 'Var',
                    'category': 'viata_de_roman',
                    'status': 'batch',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'unele tencuieli folosesc var',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_tencuiala',
                    'edge_dst': 'n_v1_19_var',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://my.baumit.ro/produse-tencuieli-decorative-vopsele-%C8%99i-gleturi'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v24_home_structure_perete',
                    'label': 'Perete',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'part_of',
                    'claim_to_verify': 'poate forma un strat pe perete',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_tencuiala',
                    'edge_dst': 'n_v24_home_structure_perete',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://dexonline.ro/definitie/tencuial%C4%83/json'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v4art_vopsea',
                    'label': 'Vopsea',
                    'category': 'arta_cultura',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'suprafața tencuită poate primi un strat de vopsea',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_tencuiala',
                    'edge_dst': 'n_v4art_vopsea',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://www.cemix.ro/ro/p/2000-Tencuieli-de-baza/2023-MP-503-A'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'}],
  'source_acquisition_note': 'Manufacturer page fetched directly. Only material/substrate/finish '
                             'relationships adopted;no standards,numerics,application or safety '
                             'instructions. Baumit catalogue opened through web '
                             'reader,lines98–101;var binding corrected before the original '
                             'five-minute clock expired,without restarting it. No claim that CEMIX '
                             'MP503A itself contains var.',
  'current_graph_counts': {'distinct': 4, 'old_main': 2, 'same_category': 3, 'batch': 2},
  'frequency': {'url': 'https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/ro/ro_50k.txt',
                'best_rank': None,
                'matched_form': None,
                'role': 'Positive signal only; absence does not reject concrete everyday/school '
                        'vocabulary.'},
  'scope': 'Accepted after both once-only independent whole-batch web reviews and explicit verdict '
           'application;reviewed/unapplied/not_landed. No game round,target,recipe,route or '
           'runtime qualification.',
  'review_verdicts': {'factual': {'verdict': 'accept',
                                  'rationale': 'Este stratul de mortar pentru suprafețe; familia '
                                               'tencuieli/tencuielii și utilizările calificate '
                                               'sunt confirmate.'},
                      'quality': {'verdict': 'accept',
                                  'rationale': 'A familiar wall finish in current Romanian '
                                               'building vocabulary; the material layer is '
                                               'distinct from the action and all ordinary keys are '
                                               'supported.'}}},
 {'id': 'v119-var',
  'lemma': 'Var',
  'kind': 'new_shared_concept',
  'node_id': 'n_v1_19_var',
  'games': ['Cald sau Rece', 'Lanțul Cuvintelor', 'Conexiuni', 'Intrusul'],
  'sense': 'Material de construcție obținut din roci calcaroase,inclusiv forma hidratată;pluralul '
           'varuri se referă la sortimente,nu unitatea electrică var.',
  'register': 'Selected everyday workshop/craft noun sense; unrelated,archaic/poetic-only meanings '
              'excluded;no instructions or clinical ruling.',
  'verified_forms': ['var', 'varul', 'varuri', 'varurile', 'varului', 'varurilor'],
  'proposed_forms': ['var', 'varul', 'varuri', 'varurile', 'varului', 'varurilor'],
  'already_resolved_forms': [],
  'already_reserved_forms': [],
  'excluded_form_hypotheses': [],
  'dictionaries': [{'lemma': 'var',
                    'url': 'https://dexonline.ro/definitie/var/json',
                    'dex_definition_ids': ['825116'],
                    'doom3_definition_ids': ['1263338'],
                    'flexion_url': 'https://dexonline.ro/definitie/var',
                    'flexion_authority': 'DOR table explicitly labelled var (material),matching '
                                         'DOOM3 sortal varuri',
                    'forms_note': 'Six ordinary normalized keys;masculine unit vari and elisions '
                                  'excluded;plural denotes sorts.',
                    'paraphrase': 'Material de construcție obținut din roci calcaroase,inclusiv '
                                  'forma hidratată;pluralul varuri se referă la sortimente,nu '
                                  'unitatea electrică var.; selected DEX sense/register and DOOM3 '
                                  'lexical gender/number checked, ordinary forms from DOR table '
                                  'explicitly labelled var (material),matching DOOM3 sortal '
                                  'varuri.'}],
  'sources': [{'url': 'https://dexonline.ro/definitie/var/json',
               'paraphrase': 'Material de construcție obținut din roci calcaroase,inclusiv forma '
                             'hidratată;pluralul varuri se referă la sortimente,nu unitatea '
                             'electrică var.; selected DEX sense/register and DOOM3 lexical '
                             'gender/number checked, ordinary forms from DOR table explicitly '
                             'labelled var (material),matching DOOM3 sortal varuri.'},
              {'url': 'https://ro.wiktionary.org/wiki/var',
               'paraphrase': 'Sensul material are varuri/varului/varurilor și este separat de '
                             'unitatea cu plural vari.'},
              {'url': 'https://www.manual.digital/89989.pdf',
               'paraphrase': 'Manualul de chimie explică obținerea varului din piatră de var și '
                             'reacția varului nestins cu apa în secțiunea explicativă;nu sunt '
                             'adoptate enunțurile-capcană din evaluare.'},
              {'url': 'https://my.baumit.ro/produse-tencuieli-decorative-vopsele-%C8%99i-gleturi',
               'paraphrase': 'Catalogul producătorului descrie explicit o tencuială pe bază de '
                             'var;pagina web citită la Tencuială este reutilizată.'}],
  'link_targets': [{'node_id': 'n_v1_19_tencuiala',
                    'label': 'Tencuială',
                    'category': 'viata_de_roman',
                    'status': 'batch',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'unele tencuieli folosesc var',
                    'direction': 'incoming',
                    'edge_src': 'n_v1_19_tencuiala',
                    'edge_dst': 'n_v1_19_var',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://my.baumit.ro/produse-tencuieli-decorative-vopsele-%C8%99i-gleturi'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v24_home_structure_perete',
                    'label': 'Perete',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'poate fi folosit la albirea pereților',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_var',
                    'edge_dst': 'n_v24_home_structure_perete',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://dexonline.ro/definitie/var/json'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v28_nature_material_piatra',
                    'label': 'Piatră',
                    'category': 'stiinta',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'se poate obține prin arderea pietrei de calcar',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_var',
                    'edge_dst': 'n_v28_nature_material_piatra',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://www.manual.digital/89989.pdf',
                                'https://dexonline.ro/definitie/var/json'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v4gas_apa',
                    'label': 'Apă',
                    'category': 'gastronomie',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'varul nestins reacționează cu apa',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_var',
                    'edge_dst': 'n_v4gas_apa',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://www.manual.digital/89989.pdf',
                                'https://dexonline.ro/definitie/var/json'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'}],
  'source_acquisition_note': 'School PDF fetched directly and text extracted in memory;only '
                             'explanatory reaction/limestone statements used,not experimental '
                             'directions,numbers or true/false prompts. The generic water reaction '
                             'also applies to potable water at the served Apă endpoint;this subset '
                             'connection is an explicit inference,not a source quote or '
                             'drinking/treatment instruction.',
  'number_scope': 'Varuri is a normative sortal plural for the construction material;vari is a '
                  'different sense.',
  'current_graph_counts': {'distinct': 4, 'old_main': 3, 'same_category': 2, 'batch': 1},
  'frequency': {'url': 'https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/ro/ro_50k.txt',
                'best_rank': 13289,
                'matched_form': 'varul',
                'role': 'Positive signal only; absence does not reject concrete everyday/school '
                        'vocabulary.'},
  'scope': 'Accepted after both once-only independent whole-batch web reviews and explicit verdict '
           'application;reviewed/unapplied/not_landed. No game round,target,recipe,route or '
           'runtime qualification.',
  'review_verdicts': {'factual': {'verdict': 'accept',
                                  'rationale': 'Este materialul de construcție; paradigma neutră '
                                               'are varuri pentru sorturi și exclude unitatea de '
                                               'măsură masculină.'},
                      'quality': {'verdict': 'accept',
                                  'rationale': 'School chemistry and a primary-school Tom Sawyer '
                                               'passage support cross-generational familiarity; '
                                               'varuri denotes sorts of the material.'}}},
 {'id': 'v119-scandura',
  'lemma': 'Scândură',
  'kind': 'new_shared_concept',
  'node_id': 'n_v1_19_scandura',
  'games': ['Cald sau Rece', 'Lanțul Cuvintelor', 'Conexiuni', 'Intrusul'],
  'sense': 'Piesă lată de lemn pentru construcții și tâmplărie;nu expresiile figurate despre '
           'oameni.',
  'register': 'Selected everyday workshop/craft noun sense; unrelated,archaic/poetic-only meanings '
              'excluded;no instructions or clinical ruling.',
  'verified_forms': ['scândură', 'scânduri', 'scândurile', 'scândurii', 'scândurilor'],
  'proposed_forms': ['scândură', 'scânduri', 'scândurile', 'scândurii', 'scândurilor'],
  'already_resolved_forms': [],
  'already_reserved_forms': [],
  'excluded_form_hypotheses': [],
  'dictionaries': [{'lemma': 'scândură',
                    'url': 'https://dexonline.ro/definitie/sc%C3%A2ndur%C4%83/json',
                    'dex_definition_ids': ['839763'],
                    'doom3_definition_ids': ['1273127'],
                    'flexion_url': 'https://dexonline.ro/definitie/sc%C3%A2ndur%C4%83',
                    'flexion_authority': 'DOR feminine Scândură table matching DOOM3 '
                                         'scânduri/scândurii',
                    'forms_note': 'Five ordinary normalized keys;elisions and regional variants '
                                  'excluded.',
                    'paraphrase': 'Piesă lată de lemn pentru construcții și tâmplărie;nu '
                                  'expresiile figurate despre oameni.; selected DEX sense/register '
                                  'and DOOM3 lexical gender/number checked, ordinary forms from '
                                  'DOR feminine Scândură table matching DOOM3 '
                                  'scânduri/scândurii.'}],
  'sources': [{'url': 'https://dexonline.ro/definitie/sc%C3%A2ndur%C4%83/json',
               'paraphrase': 'Piesă lată de lemn pentru construcții și tâmplărie;nu expresiile '
                             'figurate despre oameni.; selected DEX sense/register and DOOM3 '
                             'lexical gender/number checked, ordinary forms from DOR feminine '
                             'Scândură table matching DOOM3 scânduri/scândurii.'},
              {'url': 'https://ro.wiktionary.org/wiki/sc%C3%A2ndur%C4%83',
               'paraphrase': 'Sensul concret de piesă din lemn și paradigma '
                             'scânduri/scândurii/scândurilor sunt explicite.'},
              {'url': 'https://www.bosch-professional.com/ro/ro/panza-de-fierastrau-circular-expert-wood-cordless-pentru-fierastrau-de-banc-7561677-ocs-ac/',
               'paraphrase': 'Producătorul descrie tăierea scândurilor cu pânză de fierăstrău '
                             'circular.'},
              {'url': 'https://zep.ro/products/cuie-tapiterie-50mm-3400-buc-vorel-71983',
               'paraphrase': 'Vânzătorul descrie cuie pentru fixarea scândurilor de podea ori '
                             'acoperiș;nu se adoptă instrucțiunile de lucru.'}],
  'link_targets': [{'node_id': 'n_v1_3_material_lemn',
                    'label': 'Lemn',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'este o piesă din lemn',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_scandura',
                    'edge_dst': 'n_v1_3_material_lemn',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://dexonline.ro/definitie/sc%C3%A2ndur%C4%83/json',
                                'https://ro.wiktionary.org/wiki/sc%C3%A2ndur%C4%83'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v32_workshop_cut_fierastrau',
                    'label': 'Fierăstrău',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'poate fi tăiată cu fierăstrăul',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_scandura',
                    'edge_dst': 'n_v32_workshop_cut_fierastrau',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://www.bosch-professional.com/ro/ro/panza-de-fierastrau-circular-expert-wood-cordless-pentru-fierastrau-de-banc-7561677-ocs-ac/'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v32_workshop_fastener_cui',
                    'label': 'Cui',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'poate fi prinsă cu un cui',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_scandura',
                    'edge_dst': 'n_v32_workshop_fastener_cui',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://zep.ro/products/cuie-tapiterie-50mm-3400-buc-vorel-71983'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v24_home_surfaces_podea',
                    'label': 'Podea',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'part_of',
                    'claim_to_verify': 'poate intra în alcătuirea podelei',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_scandura',
                    'edge_dst': 'n_v24_home_surfaces_podea',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://dexonline.ro/definitie/sc%C3%A2ndur%C4%83/json',
                                'https://ro.wiktionary.org/wiki/sc%C3%A2ndur%C4%83'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'}],
  'source_acquisition_note': 'Both primary product pages fetched directly;DEX also explicitly '
                             'names the floor-board sense. No prices,specifications,safety or '
                             'cutting/fastening instructions adopted.',
  'current_graph_counts': {'distinct': 6, 'old_main': 4, 'same_category': 6, 'batch': 2},
  'frequency': {'url': 'https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/ro/ro_50k.txt',
                'best_rank': 28494,
                'matched_form': 'scândură',
                'role': 'Positive signal only; absence does not reject concrete everyday/school '
                        'vocabulary.'},
  'scope': 'Accepted after both once-only independent whole-batch web reviews and explicit verdict '
           'application;reviewed/unapplied/not_landed. No game round,target,recipe,route or '
           'runtime qualification.',
  'review_verdicts': {'factual': {'verdict': 'accept',
                                  'rationale': 'Este piesa de lemn; familia scânduri/scândurii și '
                                               'folosirea în podele sunt confirmate.'},
                      'quality': {'verdict': 'accept',
                                  'rationale': 'Ordinary timber vocabulary in school and current '
                                               'woodworking sources; the plank sense and full '
                                               'family are coherent.'}}},
 {'id': 'v119-placaj',
  'lemma': 'Placaj',
  'kind': 'new_shared_concept',
  'node_id': 'n_v1_19_placaj',
  'games': ['Cald sau Rece', 'Lanțul Cuvintelor', 'Conexiuni', 'Intrusul'],
  'sense': 'Placă alcătuită din foi de furnir lipite;nu placarea pereților sau oprirea din rugbi.',
  'register': 'Selected everyday workshop/craft noun sense; unrelated,archaic/poetic-only meanings '
              'excluded;no instructions or clinical ruling.',
  'verified_forms': ['placaj', 'placajul', 'placaje', 'placajele', 'placajului', 'placajelor'],
  'proposed_forms': ['placaj', 'placajul', 'placaje', 'placajele', 'placajului', 'placajelor'],
  'already_resolved_forms': [],
  'already_reserved_forms': [],
  'excluded_form_hypotheses': [],
  'dictionaries': [{'lemma': 'placaj',
                    'url': 'https://dexonline.ro/definitie/placaj/json',
                    'dex_definition_ids': ['872319'],
                    'doom3_definition_ids': ['1282847'],
                    'flexion_url': 'https://dexonline.ro/definitie/placaj',
                    'flexion_authority': 'DOR neuter Placaj table matching DOOM3 placaje',
                    'forms_note': 'Six ordinary normalized keys;elisions and unrelated senses '
                                  'excluded.',
                    'paraphrase': 'Placă alcătuită din foi de furnir lipite;nu placarea pereților '
                                  'sau oprirea din rugbi.; selected DEX sense/register and DOOM3 '
                                  'lexical gender/number checked, ordinary forms from DOR neuter '
                                  'Placaj table matching DOOM3 placaje.'}],
  'sources': [{'url': 'https://dexonline.ro/definitie/placaj/json',
               'paraphrase': 'Placă alcătuită din foi de furnir lipite;nu placarea pereților sau '
                             'oprirea din rugbi.; selected DEX sense/register and DOOM3 lexical '
                             'gender/number checked, ordinary forms from DOR neuter Placaj table '
                             'matching DOOM3 placaje.'},
              {'url': 'https://ro.wiktionary.org/wiki/placaj',
               'paraphrase': 'Sensul de placă din foi de furnir și paradigma '
                             'placaje/placajului/placajelor sunt explicite.'},
              {'url': 'https://www.dedeman.ro/ro/dulap-dormitor-valencia-4k2f-stejar-artisan-folie-alba-mata-4-usi-190-x-58-x-210-cm-5c/p/8093445',
               'paraphrase': 'Descrierea dulapului include placaj între materialele folosite.'},
              {'url': 'https://www.ikea.com/ro/ro/p/tonstad-scaun-fridtuna-bej-deschis-aspect-stejar-s69596253/',
               'paraphrase': 'Materialul spătarului scaunului include placaj.'},
              {'url': 'https://www.bosch-professional.com/ro/ro/panza-de-fierastrau-vertical-pro-hardwood-clean-t101aif-3076971-ocs-ac/',
               'paraphrase': 'Lista de materiale a pânzei de fierăstrău enumeră explicit placaj '
                             'multiplex,cu aceeași etichetă în textul alternativ al imaginii.'}],
  'link_targets': [{'node_id': 'n_v1_3_material_lemn',
                    'label': 'Lemn',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'este alcătuit din straturi subțiri de lemn',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_placaj',
                    'edge_dst': 'n_v1_3_material_lemn',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://dexonline.ro/definitie/placaj/json'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v24_home_storage_dulap',
                    'label': 'Dulap',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'poate fi folosit la realizarea dulapurilor',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_placaj',
                    'edge_dst': 'n_v24_home_storage_dulap',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://www.dedeman.ro/ro/dulap-dormitor-valencia-4k2f-stejar-artisan-folie-alba-mata-4-usi-190-x-58-x-210-cm-5c/p/8093445'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v24_home_seating_scaun',
                    'label': 'Scaun',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'poate fi folosit la realizarea scaunelor',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_placaj',
                    'edge_dst': 'n_v24_home_seating_scaun',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://www.ikea.com/ro/ro/p/tonstad-scaun-fridtuna-bej-deschis-aspect-stejar-s69596253/'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v32_workshop_cut_fierastrau',
                    'label': 'Fierăstrău',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'poate fi tăiat cu fierăstrăul',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_placaj',
                    'edge_dst': 'n_v32_workshop_cut_fierastrau',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://www.bosch-professional.com/ro/ro/panza-de-fierastrau-vertical-pro-hardwood-clean-t101aif-3076971-ocs-ac/'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'}],
  'source_acquisition_note': 'Cabinet,chair and qualified Bosch T101AIF sources fetched directly. '
                             'The first Bosch T308BF page lacked an explicit Placaj passage and '
                             'FEIN returned404;neither binds a claim. No prices,specifications or '
                             'directions adopted.',
  'current_graph_counts': {'distinct': 4, 'old_main': 4, 'same_category': 4, 'batch': 0},
  'frequency': {'url': 'https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/ro/ro_50k.txt',
                'best_rank': 45925,
                'matched_form': 'placaj',
                'role': 'Positive signal only; absence does not reject concrete everyday/school '
                        'vocabulary.'},
  'scope': 'Accepted after both once-only independent whole-batch web reviews and explicit verdict '
           'application;reviewed/unapplied/not_landed. No game round,target,recipe,route or '
           'runtime qualification.',
  'review_verdicts': {'factual': {'verdict': 'accept',
                                  'rationale': 'Este placa din furnire lipite, cu paradigma neutră '
                                               'placaje; învelișul și placajul de rugby nu sunt '
                                               'selectate.'},
                      'quality': {'verdict': 'accept',
                                  'rationale': 'A concrete furniture/workshop material; plywood '
                                               'use is confirmed by current chair materials and '
                                               'Bosch material image labels, without admitting '
                                               'rugby senses.'}}},
 {'id': 'v119-sipca',
  'lemma': 'Șipcă',
  'kind': 'new_shared_concept',
  'node_id': 'n_v1_19_sipca',
  'games': ['Cald sau Rece', 'Lanțul Cuvintelor', 'Conexiuni', 'Intrusul'],
  'sense': 'Bucată lungă și îngustă de lemn folosită în tâmplărie și dulgherie;nu piesele metalice '
           'numite comercial șipci.',
  'register': 'Selected everyday workshop/craft noun sense; unrelated,archaic/poetic-only meanings '
              'excluded;no instructions or clinical ruling.',
  'verified_forms': ['șipcă', 'șipci', 'șipcile', 'șipcii', 'șipcilor'],
  'proposed_forms': ['șipcă', 'șipci', 'șipcile', 'șipcii', 'șipcilor'],
  'already_resolved_forms': [],
  'already_reserved_forms': [],
  'excluded_form_hypotheses': [{'form': 'șipcei', 'reason': 'Ipoteză neconformă cu DOOM3 șipcii.'}],
  'dictionaries': [{'lemma': 'șipcă',
                    'url': 'https://dexonline.ro/definitie/%C8%99ipc%C4%83/json',
                    'dex_definition_ids': ['837497'],
                    'doom3_definition_ids': ['1271546'],
                    'flexion_url': 'https://dexonline.ro/definitie/%C8%99ipc%C4%83',
                    'flexion_authority': 'DOR feminine Șipcă table matching DOOM3 șipci/șipcii',
                    'forms_note': 'Five ordinary normalized keys;wrong șipcei,elisions and '
                                  'variants excluded.',
                    'paraphrase': 'Bucată lungă și îngustă de lemn folosită în tâmplărie și '
                                  'dulgherie;nu piesele metalice numite comercial șipci.; selected '
                                  'DEX sense/register and DOOM3 lexical gender/number checked, '
                                  'ordinary forms from DOR feminine Șipcă table matching DOOM3 '
                                  'șipci/șipcii.'}],
  'sources': [{'url': 'https://dexonline.ro/definitie/%C8%99ipc%C4%83/json',
               'paraphrase': 'Bucată lungă și îngustă de lemn folosită în tâmplărie și '
                             'dulgherie;nu piesele metalice numite comercial șipci.; selected DEX '
                             'sense/register and DOOM3 lexical gender/number checked, ordinary '
                             'forms from DOR feminine Șipcă table matching DOOM3 șipci/șipcii.'},
              {'url': 'https://ro.wiktionary.org/wiki/%C8%99ipc%C4%83',
               'paraphrase': 'Sensul din lemn și paradigma șipci/șipcii/șipcilor sunt explicite.'},
              {'url': 'https://catalog.manualedigitaleart.ro/art-romana-3-2021/v1/art-romana-3-2021.pdf',
               'paraphrase': 'Micul dicționar din manualul de română clasa3 explică șipca prin '
                             'scândură lungă și îngustă.'},
              {'url': 'https://media.hornbach.ro/cms/ro/brosura-tehnica-baterii-cuielor.pdf',
               'paraphrase': 'Broșura vânzătorului numește explicit fixarea șipcilor cu cuie.'},
              {'url': 'https://www.wienerberger.ro/content/dam/wienerberger/romania/marketing/documents-magazines/brochures/Instructiuni%20de%20montaj%20tigla%20cu%20falt%20lateral%20si%20superior.pdf',
               'paraphrase': 'Manualul ceramic de acoperiș citit la Țiglă descrie suportul din '
                             'șipci de lemn;reutilizare explicită,nu refetch.'}],
  'link_targets': [{'node_id': 'n_v1_19_scandura',
                    'label': 'Scândură',
                    'category': 'viata_de_roman',
                    'status': 'batch',
                    'relation_hypothesis': 'is_a',
                    'claim_to_verify': 'este o scândură îngustă',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_sipca',
                    'edge_dst': 'n_v1_19_scandura',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://catalog.manualedigitaleart.ro/art-romana-3-2021/v1/art-romana-3-2021.pdf'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v1_3_material_lemn',
                    'label': 'Lemn',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'este făcută din lemn',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_sipca',
                    'edge_dst': 'n_v1_3_material_lemn',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://dexonline.ro/definitie/%C8%99ipc%C4%83/json'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v32_workshop_fastener_cui',
                    'label': 'Cui',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'poate fi prinsă cu un cui',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_sipca',
                    'edge_dst': 'n_v32_workshop_fastener_cui',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://media.hornbach.ro/cms/ro/brosura-tehnica-baterii-cuielor.pdf'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v24_home_structure_acoperis',
                    'label': 'Acoperiș',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'poate susține învelitoarea acoperișului',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_sipca',
                    'edge_dst': 'n_v24_home_structure_acoperis',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://www.wienerberger.ro/content/dam/wienerberger/romania/marketing/documents-magazines/brochures/Instructiuni%20de%20montaj%20tigla%20cu%20falt%20lateral%20si%20superior.pdf'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'}],
  'source_acquisition_note': 'School and nail PDFs fetched directly,text extracted in memory. '
                             'Roof-manual cache from tick3 reused. No old regional Scriban entry '
                             'needed for the parent link;current primary-school definition '
                             'supplies it. No dimensions or construction advice adopted.',
  'current_graph_counts': {'distinct': 4, 'old_main': 3, 'same_category': 4, 'batch': 1},
  'frequency': {'url': 'https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/ro/ro_50k.txt',
                'best_rank': None,
                'matched_form': None,
                'role': 'Positive signal only; absence does not reject concrete everyday/school '
                        'vocabulary.'},
  'scope': 'Accepted after both once-only independent whole-batch web reviews and explicit verdict '
           'application;reviewed/unapplied/not_landed. No game round,target,recipe,route or '
           'runtime qualification.',
  'review_verdicts': {'factual': {'verdict': 'accept',
                                  'rationale': 'Este piesa lungă și îngustă de lemn; manualul '
                                               'școlar susține clasificarea ca scândură și DOOM3 '
                                               'familia șipci/șipcii.'},
                      'quality': {'verdict': 'accept',
                                  'rationale': 'Explicitly glossed in a Romanian grade-three '
                                               'reader and used in roof documentation; this is '
                                               'ordinary school/craft vocabulary.'}}},
 {'id': 'v119-degetar',
  'lemma': 'Degetar',
  'kind': 'new_shared_concept',
  'node_id': 'n_v1_19_degetar',
  'games': ['Cald sau Rece', 'Lanțul Cuvintelor', 'Conexiuni', 'Intrusul', 'Perechi'],
  'sense': 'Căpăcel purtat pe deget la cusut;nu planta Digitalis sau accesoriul de pescuit.',
  'register': 'Selected everyday workshop/craft noun sense; unrelated,archaic/poetic-only meanings '
              'excluded;no instructions or clinical ruling.',
  'verified_forms': ['degetar',
                     'degetarul',
                     'degetare',
                     'degetarele',
                     'degetarului',
                     'degetarelor'],
  'proposed_forms': ['degetar',
                     'degetarul',
                     'degetare',
                     'degetarele',
                     'degetarului',
                     'degetarelor'],
  'already_resolved_forms': [],
  'already_reserved_forms': [],
  'excluded_form_hypotheses': [],
  'dictionaries': [{'lemma': 'degetar',
                    'url': 'https://dexonline.ro/definitie/degetar/json',
                    'dex_definition_ids': ['856902'],
                    'doom3_definition_ids': ['1306156'],
                    'flexion_url': 'https://dexonline.ro/definitie/degetar',
                    'flexion_authority': 'DOR neuter Degetar table matching DOOM3 degetare',
                    'forms_note': 'Six ordinary normalized keys;plant aliases,vocatives,elisions '
                                  'and regional variants excluded.',
                    'paraphrase': 'Căpăcel purtat pe deget la cusut;nu planta Digitalis sau '
                                  'accesoriul de pescuit.; selected DEX sense/register and DOOM3 '
                                  'lexical gender/number checked, ordinary forms from DOR neuter '
                                  'Degetar table matching DOOM3 degetare.'}],
  'sources': [{'url': 'https://dexonline.ro/definitie/degetar/json',
               'paraphrase': 'Căpăcel purtat pe deget la cusut;nu planta Digitalis sau accesoriul '
                             'de pescuit.; selected DEX sense/register and DOOM3 lexical '
                             'gender/number checked, ordinary forms from DOR neuter Degetar table '
                             'matching DOOM3 degetare.'},
              {'url': 'https://ro.wiktionary.org/wiki/degetar',
               'paraphrase': 'Sensul de ustensilă de cusut și paradigma '
                             'degetare/degetarului/degetarelor sunt distincte de planta omonimă.'},
              {'url': 'https://intern.anc.edu.ro/virtualanc/crud/standarde/spp/brain/upload/SPP_niv%204_Tehn%20in%20ind%20textila.pdf',
               'paraphrase': 'Documentul oficial pentru industria textilă include degetarul în '
                             'trusa de croitorie pentru realizarea cusăturilor și produselor de '
                             'îmbrăcăminte.'},
              {'url': 'https://catalog.manualedigitaleart.ro/art-arte-3-2021/v1/art-arte-3-2021.pdf',
               'paraphrase': 'Lecția Micul croitor,tipărit p82,explică îmbrăcămintea și cusutul cu '
                             'ac și ață și întreabă explicit despre folosirea degetarului în '
                             'această activitate.'}],
  'link_targets': [{'node_id': 'n_v24_body_limbs_deget',
                    'label': 'Deget',
                    'category': 'stiinta',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'se poartă pe un deget la cusut',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_degetar',
                    'edge_dst': 'n_v24_body_limbs_deget',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://dexonline.ro/definitie/degetar/json'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v4sti_metal',
                    'label': 'metal',
                    'category': 'stiinta',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'poate fi făcut din metal',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_degetar',
                    'edge_dst': 'n_v4sti_metal',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://dexonline.ro/definitie/degetar/json'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v1_11_ata',
                    'label': 'Ață',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'protejează degetul la coaserea cu ață',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_degetar',
                    'edge_dst': 'n_v1_11_ata',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://catalog.manualedigitaleart.ro/art-arte-3-2021/v1/art-arte-3-2021.pdf',
                                'https://dexonline.ro/definitie/degetar/json'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v29_clothing_everyday_haina',
                    'label': 'Haină',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'poate fi folosit la cusutul hainelor',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_degetar',
                    'edge_dst': 'n_v29_clothing_everyday_haina',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://catalog.manualedigitaleart.ro/art-arte-3-2021/v1/art-arte-3-2021.pdf',
                                'https://dexonline.ro/definitie/degetar/json'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'}],
  'source_acquisition_note': 'ANC PDF fetched directly but scanned extraction/reader body '
                             'empty;indexed kit-and-garments passage only,not a full text read. '
                             'Primary school arts PDF fetched directly and readable lesson Micul '
                             'croitor,printed p82,checked including explicit degetar '
                             'prompt,needle/thread sewing and garments. No clinical or safety '
                             'ruling adopted.',
  'current_graph_counts': {'distinct': 4, 'old_main': 4, 'same_category': 2, 'batch': 0},
  'frequency': {'url': 'https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/ro/ro_50k.txt',
                'best_rank': None,
                'matched_form': None,
                'role': 'Positive signal only; absence does not reject concrete everyday/school '
                        'vocabulary.'},
  'scope': 'Accepted after both once-only independent whole-batch web reviews and explicit verdict '
           'application;reviewed/unapplied/not_landed. No game round,target,recipe,route or '
           'runtime qualification.',
  'review_verdicts': {'factual': {'verdict': 'accept',
                                  'rationale': 'Este obiectul de protecție purtat la cusut, nu '
                                               'planta; paradigma neutră degetare este '
                                               'confirmată.'},
                      'quality': {'verdict': 'accept',
                                  'rationale': 'The sewing thimble is prompted in Romanian '
                                               'grade-three arts and Romanian-language primary '
                                               'craft lessons; the plant sense is excluded.'}}},
 {'id': 'v119-croseta',
  'lemma': 'Croșetă',
  'kind': 'new_shared_concept',
  'node_id': 'n_v1_19_croseta',
  'games': ['Cald sau Rece', 'Lanțul Cuvintelor', 'Conexiuni', 'Intrusul', 'Perechi'],
  'sense': 'Ac cu cârlig pentru lucrul manual cu fire textile;nu unealta de turnătorie,piesa de '
           'îmbinare,paranteza sau ornamentul.',
  'register': 'Selected everyday workshop/craft noun sense; unrelated,archaic/poetic-only meanings '
              'excluded;no instructions or clinical ruling.',
  'verified_forms': ['croșetă', 'croșete', 'croșetele', 'croșetei', 'croșetelor'],
  'proposed_forms': ['croșetă', 'croșete', 'croșetele', 'croșetei', 'croșetelor'],
  'already_resolved_forms': [],
  'already_reserved_forms': [],
  'excluded_form_hypotheses': [],
  'dictionaries': [{'lemma': 'croșetă',
                    'url': 'https://dexonline.ro/definitie/cro%C8%99et%C4%83/json',
                    'dex_definition_ids': ['854026'],
                    'doom3_definition_ids': ['1315991'],
                    'flexion_url': 'https://dexonline.ro/definitie/cro%C8%99et%C4%83',
                    'flexion_authority': 'DOR feminine Croșetă noun table matching DOOM3 '
                                         'croșetei/croșete',
                    'forms_note': 'Five ordinary normalized keys;verb forms,neuter variant and '
                                  'other senses excluded.',
                    'paraphrase': 'Ac cu cârlig pentru lucrul manual cu fire textile;nu unealta de '
                                  'turnătorie,piesa de îmbinare,paranteza sau ornamentul.; '
                                  'selected DEX sense/register and DOOM3 lexical gender/number '
                                  'checked, ordinary forms from DOR feminine Croșetă noun table '
                                  'matching DOOM3 croșetei/croșete.'}],
  'sources': [{'url': 'https://dexonline.ro/definitie/cro%C8%99et%C4%83/json',
               'paraphrase': 'Ac cu cârlig pentru lucrul manual cu fire textile;nu unealta de '
                             'turnătorie,piesa de îmbinare,paranteza sau ornamentul.; selected DEX '
                             'sense/register and DOOM3 lexical gender/number checked, ordinary '
                             'forms from DOR feminine Croșetă noun table matching DOOM3 '
                             'croșetei/croșete.'},
              {'url': 'https://ro.wiktionary.org/wiki/cro%C8%99et%C4%83',
               'paraphrase': 'Sensul de ac pentru fire textile și paradigma '
                             'croșete/croșetei/croșetelor sunt explicite.'},
              {'url': 'https://www.educatieonline.md/Files/Manuals/4/IV_Educatia%20tenhologica%20%28a.%202017%2C%20in%20limba%20romana%29.pdf',
               'paraphrase': 'Lecția de croșetare manuală descrie lucrul cu croșeta și firul '
                             'textil,iar glosarul definește croșeta cu cârlig și dantela din ață '
                             'de bumbac;legătura cu lâna este susținută separat de produsul '
                             'actual.'},
              {'url': 'https://www.magiafirului.ro/fire/merinocot-fir-de-merinos-cu-bumbac-24.html',
               'paraphrase': 'Firul de lână și bumbac al vânzătorului este destinat și '
                             'croșetării,confirmând materialele în uzul actual.'}],
  'link_targets': [{'node_id': 'n_v1_11_lana',
                    'label': 'Lână',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'poate lucra fire din lână',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_croseta',
                    'edge_dst': 'n_v1_11_lana',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://www.educatieonline.md/Files/Manuals/4/IV_Educatia%20tenhologica%20%28a.%202017%2C%20in%20limba%20romana%29.pdf',
                                'https://www.magiafirului.ro/fire/merinocot-fir-de-merinos-cu-bumbac-24.html'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v1_11_ata',
                    'label': 'Ață',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'lucrează un fir de ață cu ajutorul cârligului',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_croseta',
                    'edge_dst': 'n_v1_11_ata',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://www.educatieonline.md/Files/Manuals/4/IV_Educatia%20tenhologica%20%28a.%202017%2C%20in%20limba%20romana%29.pdf',
                                'https://dexonline.ro/definitie/cro%C8%99et%C4%83/json'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v4sti_metal',
                    'label': 'metal',
                    'category': 'stiinta',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'poate fi fabricată din metal',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_croseta',
                    'edge_dst': 'n_v4sti_metal',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://dexonline.ro/definitie/cro%C8%99et%C4%83/json'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v1_11_bumbac',
                    'label': 'Bumbac',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'poate lucra fire din bumbac',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_croseta',
                    'edge_dst': 'n_v1_11_bumbac',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://www.educatieonline.md/Files/Manuals/4/IV_Educatia%20tenhologica%20%28a.%202017%2C%20in%20limba%20romana%29.pdf',
                                'https://www.magiafirului.ro/fire/merinocot-fir-de-merinos-cu-bumbac-24.html'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'}],
  'source_acquisition_note': 'Romanian-language grade4 school PDF and seller yarn page fetched '
                             'directly. School source is from the Republic of Moldova;Romanian '
                             'lexical norm remains DEX/DOOM3. First MEC PDF timed out and binds no '
                             'claim. No quantities,procedural,safety or marketing claims adopted.',
  'current_graph_counts': {'distinct': 5, 'old_main': 4, 'same_category': 4, 'batch': 1},
  'frequency': {'url': 'https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/ro/ro_50k.txt',
                'best_rank': None,
                'matched_form': None,
                'role': 'Positive signal only; absence does not reject concrete everyday/school '
                        'vocabulary.'},
  'scope': 'Accepted after both once-only independent whole-batch web reviews and explicit verdict '
           'application;reviewed/unapplied/not_landed. No game round,target,recipe,route or '
           'runtime qualification.',
  'review_verdicts': {'factual': {'verdict': 'accept',
                                  'rationale': 'Este acul cu cârlig pentru fire textile; paradigma '
                                               'feminină este confirmată, fără sensurile tehnice '
                                               'distincte.'},
                      'quality': {'verdict': 'accept',
                                  'rationale': 'A school/cross-generational craft tool with '
                                               'current yarn compatibility evidence; other '
                                               'technical and punctuation senses stay outside this '
                                               'concept.'}}},
 {'id': 'v119-ghem',
  'lemma': 'Ghem',
  'kind': 'new_shared_concept',
  'node_id': 'n_v1_19_ghem',
  'games': ['Cald sau Rece', 'Lanțul Cuvintelor', 'Conexiuni', 'Intrusul'],
  'sense': 'Înfășurare de fire textile de formă aproximativ rotundă;nu jocul de tenis sau sensul '
           'anatomic.',
  'register': 'Selected everyday workshop/craft noun sense; unrelated,archaic/poetic-only meanings '
              'excluded;no instructions or clinical ruling.',
  'verified_forms': ['ghem', 'ghemul', 'gheme', 'ghemele', 'ghemului', 'ghemelor'],
  'proposed_forms': ['ghem', 'ghemul', 'gheme', 'ghemele', 'ghemului', 'ghemelor'],
  'already_resolved_forms': [],
  'already_reserved_forms': [],
  'excluded_form_hypotheses': [],
  'dictionaries': [{'lemma': 'ghem',
                    'url': 'https://dexonline.ro/definitie/ghem/json',
                    'dex_definition_ids': ['877758'],
                    'doom3_definition_ids': ['1324808'],
                    'flexion_url': 'https://dexonline.ro/definitie/ghem',
                    'flexion_authority': 'DOOM3 table explicitly labelled ghem (înfășurare de '
                                         'fire),gheme',
                    'forms_note': 'Six ordinary normalized keys;tennis ghemuri/game-uri and '
                                  'secondary older -uri paradigm excluded.',
                    'paraphrase': 'Înfășurare de fire textile de formă aproximativ rotundă;nu '
                                  'jocul de tenis sau sensul anatomic.; selected DEX '
                                  'sense/register and DOOM3 lexical gender/number checked, '
                                  'ordinary forms from DOOM3 table explicitly labelled ghem '
                                  '(înfășurare de fire),gheme.'}],
  'sources': [{'url': 'https://dexonline.ro/definitie/ghem/json',
               'paraphrase': 'Înfășurare de fire textile de formă aproximativ rotundă;nu jocul de '
                             'tenis sau sensul anatomic.; selected DEX sense/register and DOOM3 '
                             'lexical gender/number checked, ordinary forms from DOOM3 table '
                             'explicitly labelled ghem (înfășurare de fire),gheme.'},
              {'url': 'https://ro.wiktionary.org/wiki/ghem',
               'paraphrase': 'Sensul de fire înfășurate este confirmat,dar pluralul său -uri nu '
                             'este adoptat deoarece DOOM3 selectează gheme.'},
              {'url': 'https://www.educatieonline.md/Files/Manuals/4/IV_Educatia%20tenhologica%20%28a.%202017%2C%20in%20limba%20romana%29.pdf',
               'paraphrase': 'Manualul descrie ghemul de ață și firul din ghem în timpul '
                             'croșetării;capitolul de tricotare include fire naturale de lână și '
                             'bumbac.'},
              {'url': 'https://www.magiafirului.ro/fire/merinocot-fir-de-merinos-cu-bumbac-24.html',
               'paraphrase': 'Firul actual de lână și bumbac este comercializat în gheme și '
                             'folosit și la croșetat;nu sunt adoptate cantitățile recomandate.'}],
  'link_targets': [{'node_id': 'n_v1_11_lana',
                    'label': 'Lână',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'poate conține fir de lână înfășurat',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_ghem',
                    'edge_dst': 'n_v1_11_lana',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://dexonline.ro/definitie/ghem/json'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v1_11_ata',
                    'label': 'Ață',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'poate fi format din ață înfășurată',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_ghem',
                    'edge_dst': 'n_v1_11_ata',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://dexonline.ro/definitie/ghem/json'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v1_11_bumbac',
                    'label': 'Bumbac',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'poate conține fir din bumbac',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_ghem',
                    'edge_dst': 'n_v1_11_bumbac',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://www.educatieonline.md/Files/Manuals/4/IV_Educatia%20tenhologica%20%28a.%202017%2C%20in%20limba%20romana%29.pdf',
                                'https://www.magiafirului.ro/fire/merinocot-fir-de-merinos-cu-bumbac-24.html'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v1_19_croseta',
                    'label': 'Croșetă',
                    'category': 'viata_de_roman',
                    'status': 'batch',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'firul din ghem poate fi lucrat cu o croșetă',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_ghem',
                    'edge_dst': 'n_v1_19_croseta',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://www.educatieonline.md/Files/Manuals/4/IV_Educatia%20tenhologica%20%28a.%202017%2C%20in%20limba%20romana%29.pdf'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'}],
  'source_acquisition_note': 'School and yarn sources are explicit cached reuse from Croșetă this '
                             'tick,not fresh requests. Only materials and ghem/crochet '
                             'relationship adopted;no procedural,numerical or body-organ claims.',
  'number_scope': 'Normative gheme for wound thread,not the sporting ghemuri.',
  'current_graph_counts': {'distinct': 4, 'old_main': 3, 'same_category': 4, 'batch': 1},
  'frequency': {'url': 'https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/ro/ro_50k.txt',
                'best_rank': 34832,
                'matched_form': 'ghem',
                'role': 'Positive signal only; absence does not reject concrete everyday/school '
                        'vocabulary.'},
  'scope': 'Accepted after both once-only independent whole-batch web reviews and explicit verdict '
           'application;reviewed/unapplied/not_landed. No game round,target,recipe,route or '
           'runtime qualification.',
  'review_verdicts': {'factual': {'verdict': 'accept',
                                  'rationale': 'Este înfășurarea de fire, cu pluralul normativ '
                                               'gheme; tenisul și forma ghemuri nu sunt admise.'},
                      'quality': {'verdict': 'accept',
                                  'rationale': 'A familiar thread/yarn ball in primary craft and '
                                               'current yarn sources; gheme is the matching '
                                               'winding-of-threads paradigm.'}}},
 {'id': 'v119-croitor',
  'lemma': 'Croitor',
  'kind': 'new_shared_concept',
  'node_id': 'n_v1_19_croitor',
  'games': ['Cald sau Rece', 'Lanțul Cuvintelor', 'Conexiuni', 'Intrusul', 'Perechi'],
  'sense': 'Meseriaș care croiește și coase haine;nu insecta sau mușchiul.',
  'register': 'Selected everyday workshop/craft noun sense; unrelated,archaic/poetic-only meanings '
              'excluded;no instructions or clinical ruling.',
  'verified_forms': ['croitor', 'croitorul', 'croitori', 'croitorii', 'croitorului', 'croitorilor'],
  'proposed_forms': ['croitor', 'croitorul', 'croitori', 'croitorii', 'croitorului', 'croitorilor'],
  'already_resolved_forms': [],
  'already_reserved_forms': [],
  'excluded_form_hypotheses': [],
  'dictionaries': [{'lemma': 'croitor',
                    'url': 'https://dexonline.ro/definitie/croitor/json',
                    'dex_definition_ids': ['853828'],
                    'doom3_definition_ids': ['1315902'],
                    'flexion_url': 'https://dexonline.ro/definitie/croitor',
                    'flexion_authority': 'DOOM3 masculine Croitor '
                                         'table,croitori/croitorului/croitorilor',
                    'forms_note': 'Six ordinary screened normalized '
                                  'keys;vocative/elisions,regional synonyms and unscreened derived '
                                  'feminine lemma excluded.',
                    'paraphrase': 'Meseriaș care croiește și coase haine;nu insecta sau mușchiul.; '
                                  'selected DEX sense/register and DOOM3 lexical gender/number '
                                  'checked, ordinary forms from DOOM3 masculine Croitor '
                                  'table,croitori/croitorului/croitorilor.'}],
  'sources': [{'url': 'https://dexonline.ro/definitie/croitor/json',
               'paraphrase': 'Meseriaș care croiește și coase haine;nu insecta sau mușchiul.; '
                             'selected DEX sense/register and DOOM3 lexical gender/number checked, '
                             'ordinary forms from DOOM3 masculine Croitor '
                             'table,croitori/croitorului/croitorilor.'},
              {'url': 'https://ro.wiktionary.org/wiki/croitor',
               'paraphrase': 'Sensul de meseriaș/muncitor și paradigma '
                             'croitori/croitorului/croitorilor sunt separate de insectă și '
                             'mușchi.'},
              {'url': 'https://catalog.manualedigitaleart.ro/art-arte-3-2021/v1/art-arte-3-2021.pdf',
               'paraphrase': 'Lecția Micul croitor,p82,descrie meseria,realizarea și repararea '
                             'hainelor și foarfeca folosită la croit;cache verificat anterior la '
                             'Degetar.'}],
  'link_targets': [{'node_id': 'n_v28_work_occupation_meserie',
                    'label': 'Meserie',
                    'category': 'societate',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'practică meseria de a croi și coase haine',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_croitor',
                    'edge_dst': 'n_v28_work_occupation_meserie',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://catalog.manualedigitaleart.ro/art-arte-3-2021/v1/art-arte-3-2021.pdf',
                                'https://dexonline.ro/definitie/croitor/json'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v4soc_munca',
                    'label': 'muncă',
                    'category': 'societate',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'munca sa include croirea și coaserea hainelor',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_croitor',
                    'edge_dst': 'n_v4soc_munca',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://catalog.manualedigitaleart.ro/art-arte-3-2021/v1/art-arte-3-2021.pdf',
                                'https://dexonline.ro/definitie/croitor/json'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v29_clothing_everyday_haina',
                    'label': 'Haină',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'confecționează sau repară haine',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_croitor',
                    'edge_dst': 'n_v29_clothing_everyday_haina',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://catalog.manualedigitaleart.ro/art-arte-3-2021/v1/art-arte-3-2021.pdf',
                                'https://dexonline.ro/definitie/croitor/json'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v1_11_foarfeca',
                    'label': 'Foarfecă',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'poate tăia materialul cu foarfeca',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_croitor',
                    'edge_dst': 'n_v1_11_foarfeca',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://catalog.manualedigitaleart.ro/art-arte-3-2021/v1/art-arte-3-2021.pdf',
                                'https://dexonline.ro/definitie/croitor/json'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'}],
  'source_acquisition_note': 'School lesson explicitly reused from the direct Degetar fetch this '
                             'tick. Meserie and muncă are separate existing nodes tied to the '
                             'stated occupation/work,not person-name facts. No new derivative or '
                             'regional input added.',
  'current_graph_counts': {'distinct': 4, 'old_main': 4, 'same_category': 2, 'batch': 0},
  'frequency': {'url': 'https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/ro/ro_50k.txt',
                'best_rank': 19921,
                'matched_form': 'croitor',
                'role': 'Positive signal only; absence does not reject concrete everyday/school '
                        'vocabulary.'},
  'scope': 'Accepted after both once-only independent whole-batch web reviews and explicit verdict '
           'application;reviewed/unapplied/not_landed. No game round,target,recipe,route or '
           'runtime qualification.',
  'review_verdicts': {'factual': {'verdict': 'accept',
                                  'rationale': 'Este meseriașul care confecționează haine, cu '
                                               'paradigma masculină; insecta și mușchiul nu sunt '
                                               'selectate.'},
                      'quality': {'verdict': 'accept',
                                  'rationale': 'A familiar occupation explicitly defined in '
                                               'Romanian grade-three arts; insect/anatomical '
                                               'meanings do not enter the shared concept.'}}},
 {'id': 'v119-tamplar',
  'lemma': 'Tâmplar',
  'kind': 'new_shared_concept',
  'node_id': 'n_v1_19_tamplar',
  'games': ['Cald sau Rece', 'Lanțul Cuvintelor', 'Conexiuni', 'Intrusul', 'Perechi'],
  'sense': 'Meseriaș care prelucrează lemnul pentru mobilă și alte obiecte;nu lucrătorul în '
           'tâmplărie PVC ca sens extins nesursat.',
  'register': 'Selected everyday workshop/craft noun sense; unrelated,archaic/poetic-only meanings '
              'excluded;no instructions or clinical ruling.',
  'verified_forms': ['tâmplar', 'tâmplarul', 'tâmplari', 'tâmplarii', 'tâmplarului', 'tâmplarilor'],
  'proposed_forms': ['tâmplar', 'tâmplarul', 'tâmplari', 'tâmplarii', 'tâmplarului', 'tâmplarilor'],
  'already_resolved_forms': [],
  'already_reserved_forms': [],
  'excluded_form_hypotheses': [],
  'dictionaries': [{'lemma': 'tâmplar',
                    'url': 'https://dexonline.ro/definitie/t%C3%A2mplar/json',
                    'dex_definition_ids': ['831431'],
                    'doom3_definition_ids': ['1267402'],
                    'flexion_url': 'https://dexonline.ro/definitie/t%C3%A2mplar',
                    'flexion_authority': 'DOOM3 masculine Tâmplar '
                                         'table,tâmplari/tâmplarului/tâmplarilor',
                    'forms_note': 'Six ordinary screened normalized keys;vocatives,elisions and '
                                  'unscreened regional Stoler family excluded.',
                    'paraphrase': 'Meseriaș care prelucrează lemnul pentru mobilă și alte '
                                  'obiecte;nu lucrătorul în tâmplărie PVC ca sens extins '
                                  'nesursat.; selected DEX sense/register and DOOM3 lexical '
                                  'gender/number checked, ordinary forms from DOOM3 masculine '
                                  'Tâmplar table,tâmplari/tâmplarului/tâmplarilor.'}],
  'sources': [{'url': 'https://dexonline.ro/definitie/t%C3%A2mplar/json',
               'paraphrase': 'Meseriaș care prelucrează lemnul pentru mobilă și alte obiecte;nu '
                             'lucrătorul în tâmplărie PVC ca sens extins nesursat.; selected DEX '
                             'sense/register and DOOM3 lexical gender/number checked, ordinary '
                             'forms from DOOM3 masculine Tâmplar '
                             'table,tâmplari/tâmplarului/tâmplarilor.'},
              {'url': 'https://ro.wiktionary.org/wiki/t%C3%A2mplar',
               'paraphrase': 'Ocupația este definită prin meseriaș/muncitor care lucrează '
                             'lemnul;paradigma tâmplari/tâmplarului/tâmplarilor este explicită.'},
              {'url': 'https://www.bosch-professional.com/ro/ro/prelucrarea-lemnului-227129-ocs-c/',
               'paraphrase': 'Producătorul leagă rindelele de prelucrarea lemnului și de '
                             'activitatea tâmplarilor.'},
              {'url': 'https://dexonline.ro/definitie/rindea/json',
               'paraphrase': 'DEX858657 Rindea descrie netezirea pieselor de lemn;tâmplar→rindea '
                             'combină ocupația și funcția uneltei.'}],
  'link_targets': [{'node_id': 'n_v28_work_occupation_meserie',
                    'label': 'Meserie',
                    'category': 'societate',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'practică meseria de prelucrare a lemnului',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_tamplar',
                    'edge_dst': 'n_v28_work_occupation_meserie',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://dexonline.ro/definitie/t%C3%A2mplar/json'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v4soc_munca',
                    'label': 'muncă',
                    'category': 'societate',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'munca sa include prelucrarea lemnului',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_tamplar',
                    'edge_dst': 'n_v4soc_munca',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://dexonline.ro/definitie/t%C3%A2mplar/json'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v1_3_material_lemn',
                    'label': 'Lemn',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'prelucrează lemnul',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_tamplar',
                    'edge_dst': 'n_v1_3_material_lemn',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://dexonline.ro/definitie/t%C3%A2mplar/json'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v1_19_rindea',
                    'label': 'Rindea',
                    'category': 'viata_de_roman',
                    'status': 'batch',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'poate netezi lemnul cu rindeaua',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_tamplar',
                    'edge_dst': 'n_v1_19_rindea',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://www.bosch-professional.com/ro/ro/prelucrarea-lemnului-227129-ocs-c/',
                                'https://dexonline.ro/definitie/rindea/json',
                                'https://dexonline.ro/definitie/t%C3%A2mplar/json'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'}],
  'source_acquisition_note': 'Bosch woodworking category fetched directly;exact Rindea JSON from '
                             'tick1 reused with its original acquisition trace. Tool link combines '
                             'directly stated occupation,tool category and smoothing function;no '
                             'marketing,specification or work instructions adopted.',
  'current_graph_counts': {'distinct': 4, 'old_main': 3, 'same_category': 2, 'batch': 1},
  'frequency': {'url': 'https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/ro/ro_50k.txt',
                'best_rank': 25519,
                'matched_form': 'tâmplar',
                'role': 'Positive signal only; absence does not reject concrete everyday/school '
                        'vocabulary.'},
  'scope': 'Accepted after both once-only independent whole-batch web reviews and explicit verdict '
           'application;reviewed/unapplied/not_landed. No game round,target,recipe,route or '
           'runtime qualification.',
  'review_verdicts': {'factual': {'verdict': 'accept',
                                  'rationale': 'Meseria de prelucrare a lemnului și familia '
                                               'masculină sunt confirmate; folosirea rindelei este '
                                               'coerentă cu sensul.'},
                      'quality': {'verdict': 'accept',
                                  'rationale': 'A familiar woodworker named in school work and '
                                               'current woodworking contexts; generic employment '
                                               'links carry no board approval.'}}},
 {'id': 'v119-fierar',
  'lemma': 'Fierar',
  'kind': 'new_shared_concept',
  'node_id': 'n_v1_19_fierar',
  'games': ['Cald sau Rece', 'Lanțul Cuvintelor', 'Conexiuni', 'Intrusul', 'Perechi'],
  'sense': 'Muncitor care prelucrează fierul sau alte metale la cald;nu sensul distinct '
           'fierar-betonist.',
  'register': 'Selected everyday workshop/craft noun sense; unrelated,archaic/poetic-only meanings '
              'excluded;no instructions or clinical ruling.',
  'verified_forms': ['fierar', 'fierarul', 'fierari', 'fierarii', 'fierarului', 'fierarilor'],
  'proposed_forms': ['fierar', 'fierarul', 'fierari', 'fierarii', 'fierarului', 'fierarilor'],
  'already_resolved_forms': [],
  'already_reserved_forms': [],
  'excluded_form_hypotheses': [],
  'dictionaries': [{'lemma': 'fierar',
                    'url': 'https://dexonline.ro/definitie/fierar/json',
                    'dex_definition_ids': ['870544'],
                    'doom3_definition_ids': ['1301480'],
                    'flexion_url': 'https://dexonline.ro/definitie/fierar',
                    'flexion_authority': 'DOOM3 masculine Fierar '
                                         'table,fierari/fierarului/fierarilor',
                    'forms_note': 'Six ordinary screened normalized '
                                  'keys;vocatives,elisions,unscreened regional inputs and '
                                  'fierar-betonist excluded.',
                    'paraphrase': 'Muncitor care prelucrează fierul sau alte metale la cald;nu '
                                  'sensul distinct fierar-betonist.; selected DEX sense/register '
                                  'and DOOM3 lexical gender/number checked, ordinary forms from '
                                  'DOOM3 masculine Fierar table,fierari/fierarului/fierarilor.'}],
  'sources': [{'url': 'https://dexonline.ro/definitie/fierar/json',
               'paraphrase': 'Muncitor care prelucrează fierul sau alte metale la cald;nu sensul '
                             'distinct fierar-betonist.; selected DEX sense/register and DOOM3 '
                             'lexical gender/number checked, ordinary forms from DOOM3 masculine '
                             'Fierar table,fierari/fierarului/fierarilor.'},
              {'url': 'https://ro.wiktionary.org/wiki/fierar',
               'paraphrase': 'Ocupația de prelucrare a metalelor și paradigma '
                             'fierari/fierarului/fierarilor sunt explicite.'},
              {'url': 'https://www.rri.ro/rubrici/vizitati-romania/muzeul-satului-isverna-id591495.html',
               'paraphrase': 'Reportajul propriu Radio România descrie fierarul cu nicovala în '
                             'atelier;cache direct deja verificat la Nicovală în tick2.'}],
  'link_targets': [{'node_id': 'n_v28_work_occupation_meserie',
                    'label': 'Meserie',
                    'category': 'societate',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'practică meseria de prelucrare a metalului',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_fierar',
                    'edge_dst': 'n_v28_work_occupation_meserie',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://dexonline.ro/definitie/fierar/json'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v4soc_munca',
                    'label': 'muncă',
                    'category': 'societate',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'munca sa include prelucrarea metalului',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_fierar',
                    'edge_dst': 'n_v4soc_munca',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://dexonline.ro/definitie/fierar/json'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v4sti_metal',
                    'label': 'metal',
                    'category': 'stiinta',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'prelucrează piese din metal',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_fierar',
                    'edge_dst': 'n_v4sti_metal',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://dexonline.ro/definitie/fierar/json'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v1_19_nicovala',
                    'label': 'Nicovală',
                    'category': 'viata_de_roman',
                    'status': 'batch',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'poate prelucra piesa pe nicovală',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_fierar',
                    'edge_dst': 'n_v1_19_nicovala',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://www.rri.ro/rubrici/vizitati-romania/muzeul-satului-isverna-id591495.html',
                                'https://dexonline.ro/definitie/fierar/json'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'}],
  'source_acquisition_note': 'RRI direct source cache from tick2 reused and relevant anvil passage '
                             'reread. Occupation/metal/tool facts only;no named people,place '
                             'history,dates,temperatures or practical directions adopted.',
  'current_graph_counts': {'distinct': 4, 'old_main': 3, 'same_category': 2, 'batch': 1},
  'frequency': {'url': 'https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/ro/ro_50k.txt',
                'best_rank': 22496,
                'matched_form': 'fierar',
                'role': 'Positive signal only; absence does not reject concrete everyday/school '
                        'vocabulary.'},
  'scope': 'Accepted after both once-only independent whole-batch web reviews and explicit verdict '
           'application;reviewed/unapplied/not_landed. No game round,target,recipe,route or '
           'runtime qualification.',
  'review_verdicts': {'factual': {'verdict': 'accept',
                                  'rationale': 'Este meseriașul de forjă, cu paradigma masculină; '
                                               'fierarul-betonist și sinonimele regionale nu sunt '
                                               'admise.'},
                      'quality': {'verdict': 'accept',
                                  'rationale': 'A living and historical Romanian craft occupation, '
                                               'evidenced by a working blacksmith and museum '
                                               'scholarship; ordinary masculine forms are '
                                               'coherent.'}}},
 {'id': 'v119-zidar',
  'lemma': 'Zidar',
  'kind': 'new_shared_concept',
  'node_id': 'n_v1_19_zidar',
  'games': ['Cald sau Rece', 'Lanțul Cuvintelor', 'Conexiuni', 'Intrusul', 'Perechi'],
  'sense': 'Muncitor specializat în lucrări de zidărie;nu personajele sau numele din exemplele '
           'literare.',
  'register': 'Selected everyday workshop/craft noun sense; unrelated,archaic/poetic-only meanings '
              'excluded;no instructions or clinical ruling.',
  'verified_forms': ['zidar', 'zidarul', 'zidari', 'zidarii', 'zidarului', 'zidarilor'],
  'proposed_forms': ['zidar', 'zidarul', 'zidari', 'zidarii', 'zidarului', 'zidarilor'],
  'already_resolved_forms': [],
  'already_reserved_forms': [],
  'excluded_form_hypotheses': [],
  'dictionaries': [{'lemma': 'zidar',
                    'url': 'https://dexonline.ro/definitie/zidar/json',
                    'dex_definition_ids': ['823850'],
                    'doom3_definition_ids': ['1316797'],
                    'flexion_url': 'https://dexonline.ro/definitie/zidar',
                    'flexion_authority': 'DOOM3 masculine Zidar table,zidari/zidarului/zidarilor',
                    'forms_note': 'Six ordinary screened normalized keys;vocatives,elisions and '
                                  'regional synonyms excluded.',
                    'paraphrase': 'Muncitor specializat în lucrări de zidărie;nu personajele sau '
                                  'numele din exemplele literare.; selected DEX sense/register and '
                                  'DOOM3 lexical gender/number checked, ordinary forms from DOOM3 '
                                  'masculine Zidar table,zidari/zidarului/zidarilor.'}],
  'sources': [{'url': 'https://dexonline.ro/definitie/zidar/json',
               'paraphrase': 'Muncitor specializat în lucrări de zidărie;nu personajele sau numele '
                             'din exemplele literare.; selected DEX sense/register and DOOM3 '
                             'lexical gender/number checked, ordinary forms from DOOM3 masculine '
                             'Zidar table,zidari/zidarului/zidarilor.'},
              {'url': 'https://ro.wiktionary.org/wiki/zidar',
               'paraphrase': 'Ocupația de muncitor specializat în zidărie și paradigma '
                             'zidari/zidarului/zidarilor sunt explicite.'},
              {'url': 'https://dexonline.ro/definitie/mistrie/json',
               'paraphrase': 'DEX890809 Mistrie definește unealta de zidărie prin întinderea '
                             'mortarului pe zid;sursă exactă reutilizată din tick1.'}],
  'link_targets': [{'node_id': 'n_v28_work_occupation_meserie',
                    'label': 'Meserie',
                    'category': 'societate',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'practică meseria de a construi zidărie',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_zidar',
                    'edge_dst': 'n_v28_work_occupation_meserie',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://dexonline.ro/definitie/zidar/json',
                                'https://ro.wiktionary.org/wiki/zidar'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v4soc_munca',
                    'label': 'muncă',
                    'category': 'societate',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'munca sa include realizarea zidăriei',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_zidar',
                    'edge_dst': 'n_v4soc_munca',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://dexonline.ro/definitie/zidar/json',
                                'https://ro.wiktionary.org/wiki/zidar'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v24_home_structure_perete',
                    'label': 'Perete',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'construiește pereți din elemente de zidărie',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_zidar',
                    'edge_dst': 'n_v24_home_structure_perete',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://dexonline.ro/definitie/zidar/json',
                                'https://dexonline.ro/definitie/mistrie/json'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v1_19_mistrie',
                    'label': 'Mistrie',
                    'category': 'viata_de_roman',
                    'status': 'batch',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'poate întinde mortarul cu mistria',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_zidar',
                    'edge_dst': 'n_v1_19_mistrie',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://dexonline.ro/definitie/zidar/json',
                                'https://dexonline.ro/definitie/mistrie/json'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'}],
  'source_acquisition_note': 'Current dictionary pages fetched directly;Mistrie JSON trace from '
                             'tick1 reused. Mason→trowel combines the exact occupation and '
                             'tool-for-masonry definitions;wall caption remains conditional on '
                             'masonry elements. No literary people/place facts or technical '
                             'instructions adopted.',
  'current_graph_counts': {'distinct': 4, 'old_main': 3, 'same_category': 2, 'batch': 1},
  'frequency': {'url': 'https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/ro/ro_50k.txt',
                'best_rank': 42321,
                'matched_form': 'zidar',
                'role': 'Positive signal only; absence does not reject concrete everyday/school '
                        'vocabulary.'},
  'scope': 'Accepted after both once-only independent whole-batch web reviews and explicit verdict '
           'application;reviewed/unapplied/not_landed. No game round,target,recipe,route or '
           'runtime qualification.',
  'review_verdicts': {'factual': {'verdict': 'accept',
                                  'rationale': 'Este meseriașul de zidărie, cu paradigma '
                                               'masculină; pereții și mistria corespund sensului.'},
                      'quality': {'verdict': 'accept',
                                  'rationale': 'A familiar building occupation with general '
                                               'Romanian and education-curriculum evidence; '
                                               'ordinary masculine forms and declared tool links '
                                               'are coherent.'}}},
 {'id': 'v119-instalator',
  'lemma': 'Instalator',
  'kind': 'new_shared_concept',
  'node_id': 'n_v1_19_instalator',
  'games': ['Cald sau Rece', 'Lanțul Cuvintelor', 'Conexiuni', 'Intrusul', 'Perechi'],
  'sense': 'Persoană specializată în montarea și repararea instalațiilor '
           'tehnico-sanitare,conductelor și aparatelor.',
  'register': 'Selected everyday workshop/craft noun sense; unrelated,archaic/poetic-only meanings '
              'excluded;no instructions or clinical ruling.',
  'verified_forms': ['instalator',
                     'instalatorul',
                     'instalatori',
                     'instalatorii',
                     'instalatorului',
                     'instalatorilor'],
  'proposed_forms': ['instalator',
                     'instalatorul',
                     'instalatori',
                     'instalatorii',
                     'instalatorului',
                     'instalatorilor'],
  'already_resolved_forms': [],
  'already_reserved_forms': [],
  'excluded_form_hypotheses': [],
  'dictionaries': [{'lemma': 'instalator',
                    'url': 'https://dexonline.ro/definitie/instalator/json',
                    'dex_definition_ids': ['877461'],
                    'doom3_definition_ids': ['1298235'],
                    'flexion_url': 'https://dexonline.ro/definitie/instalator',
                    'flexion_authority': 'DOR masculine Instalator table matching DOOM3 '
                                         'instalatori',
                    'forms_note': 'Six ordinary screened normalized keys;vocatives,elisions and '
                                  'unscreened derived feminine family excluded.',
                    'paraphrase': 'Persoană specializată în montarea și repararea instalațiilor '
                                  'tehnico-sanitare,conductelor și aparatelor.; selected DEX '
                                  'sense/register and DOOM3 lexical gender/number checked, '
                                  'ordinary forms from DOR masculine Instalator table matching '
                                  'DOOM3 instalatori.'}],
  'sources': [{'url': 'https://dexonline.ro/definitie/instalator/json',
               'paraphrase': 'Persoană specializată în montarea și repararea instalațiilor '
                             'tehnico-sanitare,conductelor și aparatelor.; selected DEX '
                             'sense/register and DOOM3 lexical gender/number checked, ordinary '
                             'forms from DOR masculine Instalator table matching DOOM3 '
                             'instalatori.'},
              {'url': 'https://ro.wiktionary.org/wiki/instalator',
               'paraphrase': 'Ocupația de specialist în montare/reparare și paradigma '
                             'instalatori/instalatorului/instalatorilor sunt explicite.'},
              {'url': 'https://instalator-cluj.ro/servicii-prestate/',
               'paraphrase': 'Lista de servicii publicată de instalator include montarea și '
                             'repararea robinetelor și țevilor;nu se adoptă calificări,garanții '
                             'sau recomandări ale prestatorului.'}],
  'link_targets': [{'node_id': 'n_v28_work_occupation_meserie',
                    'label': 'Meserie',
                    'category': 'societate',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'practică o meserie de montare și întreținere a '
                                       'instalațiilor',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_instalator',
                    'edge_dst': 'n_v28_work_occupation_meserie',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://dexonline.ro/definitie/instalator/json'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v4soc_munca',
                    'label': 'muncă',
                    'category': 'societate',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'munca sa include montarea sau repararea instalațiilor',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_instalator',
                    'edge_dst': 'n_v4soc_munca',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://dexonline.ro/definitie/instalator/json'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v33_bathroom_fixture_robinet',
                    'label': 'Robinet',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'poate monta sau repara robinete',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_instalator',
                    'edge_dst': 'n_v33_bathroom_fixture_robinet',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://instalator-cluj.ro/servicii-prestate/',
                                'https://dexonline.ro/definitie/instalator/json'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v1_19_teava',
                    'label': 'Țeavă',
                    'category': 'viata_de_roman',
                    'status': 'batch',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'poate monta sau repara țevi',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_instalator',
                    'edge_dst': 'n_v1_19_teava',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://instalator-cluj.ro/servicii-prestate/',
                                'https://dexonline.ro/definitie/instalator/json'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'}],
  'source_acquisition_note': 'First-party Romanian plumber services page fetched directly for '
                             'concrete activity examples only;no certification,person '
                             'identity,service recommendation,price or installation advice '
                             'adopted.',
  'current_graph_counts': {'distinct': 4, 'old_main': 3, 'same_category': 2, 'batch': 1},
  'frequency': {'url': 'https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/ro/ro_50k.txt',
                'best_rank': 14437,
                'matched_form': 'instalator',
                'role': 'Positive signal only; absence does not reject concrete everyday/school '
                        'vocabulary.'},
  'scope': 'Accepted after both once-only independent whole-batch web reviews and explicit verdict '
           'application;reviewed/unapplied/not_landed. No game round,target,recipe,route or '
           'runtime qualification.',
  'review_verdicts': {'factual': {'verdict': 'accept',
                                  'rationale': 'Este meseriașul de instalații tehnico-sanitare, cu '
                                               'paradigma masculină; exemplele de robinete și țevi '
                                               'sunt explicite.'},
                      'quality': {'verdict': 'accept',
                                  'rationale': 'A familiar household trade; current Romanian '
                                               'service descriptions explicitly list pipe and tap '
                                               'work, with a complete masculine family.'}}},
 {'id': 'v119-electrician',
  'lemma': 'Electrician',
  'kind': 'new_shared_concept',
  'node_id': 'n_v1_19_electrician',
  'games': ['Cald sau Rece', 'Lanțul Cuvintelor', 'Conexiuni', 'Intrusul', 'Perechi'],
  'sense': 'Persoană calificată care lucrează sau repară instalații și aparate '
           'electrice;substantivul de ocupație,nu adjectivul.',
  'register': 'Selected everyday workshop/craft noun sense; unrelated,archaic/poetic-only meanings '
              'excluded;no instructions or clinical ruling.',
  'verified_forms': ['electrician',
                     'electricianul',
                     'electricieni',
                     'electricienii',
                     'electricianului',
                     'electricienilor'],
  'proposed_forms': ['electrician',
                     'electricianul',
                     'electricieni',
                     'electricienii',
                     'electricianului',
                     'electricienilor'],
  'already_resolved_forms': [],
  'already_reserved_forms': [],
  'excluded_form_hypotheses': [],
  'dictionaries': [{'lemma': 'electrician',
                    'url': 'https://dexonline.ro/definitie/electrician/json',
                    'dex_definition_ids': ['865152'],
                    'doom3_definition_ids': ['1303592'],
                    'flexion_url': 'https://dexonline.ro/definitie/electrician',
                    'flexion_authority': 'DOOM3 masculine Electrician '
                                         'table,electricieni/electricianului/electricienilor',
                    'forms_note': 'Six ordinary screened normalized '
                                  'keys;vocatives,elisions,English forms and unscreened derived '
                                  'feminine family excluded.',
                    'paraphrase': 'Persoană calificată care lucrează sau repară instalații și '
                                  'aparate electrice;substantivul de ocupație,nu adjectivul.; '
                                  'selected DEX sense/register and DOOM3 lexical gender/number '
                                  'checked, ordinary forms from DOOM3 masculine Electrician '
                                  'table,electricieni/electricianului/electricienilor.'}],
  'sources': [{'url': 'https://dexonline.ro/definitie/electrician/json',
               'paraphrase': 'Persoană calificată care lucrează sau repară instalații și aparate '
                             'electrice;substantivul de ocupație,nu adjectivul.; selected DEX '
                             'sense/register and DOOM3 lexical gender/number checked, ordinary '
                             'forms from DOOM3 masculine Electrician '
                             'table,electricieni/electricianului/electricienilor.'},
              {'url': 'https://ro.wiktionary.org/wiki/electrician',
               'paraphrase': 'Secțiunea română confirmă ocupația și paradigma '
                             'electricieni/electricianului/electricienilor;secțiunea engleză nu '
                             'furnizează forme.'},
              {'url': 'https://www.usab-tm.ro/utilizatori/universitate/file/concursuri/2024/iul/mc_4/Fisa%20postului%20mc.calif-Electrician.pdf',
               'paraphrase': 'Fișa de post publicată de universitate pentru electrician numește '
                             'explicit instalarea prizelor și a altor dispozitive electrice.'}],
  'link_targets': [{'node_id': 'n_v28_work_occupation_meserie',
                    'label': 'Meserie',
                    'category': 'societate',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'practică o meserie din domeniul instalațiilor electrice',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_electrician',
                    'edge_dst': 'n_v28_work_occupation_meserie',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://dexonline.ro/definitie/electrician/json'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v4soc_munca',
                    'label': 'muncă',
                    'category': 'societate',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'munca sa include instalațiile electrice',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_electrician',
                    'edge_dst': 'n_v4soc_munca',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://dexonline.ro/definitie/electrician/json'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v3sti_electricitate',
                    'label': 'Electricitate',
                    'category': 'stiinta',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'lucrează cu instalații care folosesc electricitate',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_electrician',
                    'edge_dst': 'n_v3sti_electricitate',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://dexonline.ro/definitie/electrician/json'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v33_electric_outlet_priza',
                    'label': 'Priză electrică',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'poate monta sau repara prize electrice',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_electrician',
                    'edge_dst': 'n_v33_electric_outlet_priza',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://www.usab-tm.ro/utilizatori/universitate/file/concursuri/2024/iul/mc_4/Fisa%20postului%20mc.calif-Electrician.pdf',
                                'https://dexonline.ro/definitie/electrician/json'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'}],
  'source_acquisition_note': 'Primary university job-description PDF fetched directly and readable '
                             'text checked;only occupation and actual outlet-installation duty '
                             'adopted. No current vacancy,licensing,legal requirement,safety or '
                             'wiring instructions claimed.',
  'current_graph_counts': {'distinct': 4, 'old_main': 4, 'same_category': 2, 'batch': 0},
  'frequency': {'url': 'https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/ro/ro_50k.txt',
                'best_rank': 26414,
                'matched_form': 'electrician',
                'role': 'Positive signal only; absence does not reject concrete everyday/school '
                        'vocabulary.'},
  'scope': 'Accepted after both once-only independent whole-batch web reviews and explicit verdict '
           'application;reviewed/unapplied/not_landed. No game round,target,recipe,route or '
           'runtime qualification.',
  'review_verdicts': {'factual': {'verdict': 'accept',
                                  'rationale': 'Este meseriașul de instalații electrice; familia '
                                               'electricieni este confirmată și fișa postului '
                                               'numește prizele.'},
                      'quality': {'verdict': 'accept',
                                  'rationale': 'A familiar household/public-institution trade with '
                                               'current native job evidence; electricieni and its '
                                               'articulated/genitive forms follow the selected '
                                               'noun.'}}},
 {'id': 'v119-atelier',
  'lemma': 'Atelier',
  'kind': 'new_shared_concept',
  'node_id': 'n_v1_19_atelier',
  'games': ['Cald sau Rece', 'Lanțul Cuvintelor'],
  'sense': 'Spațiu dotat pentru muncă meșteșugărească ori industrială,inclusiv secția unei '
           'fabrici;nu colectivul sau evenimentul de instruire.',
  'register': 'Selected everyday workshop/craft noun sense; unrelated,archaic/poetic-only meanings '
              'excluded;no instructions or clinical ruling.',
  'verified_forms': ['atelier',
                     'atelierul',
                     'ateliere',
                     'atelierele',
                     'atelierului',
                     'atelierelor'],
  'proposed_forms': ['atelier',
                     'atelierul',
                     'ateliere',
                     'atelierele',
                     'atelierului',
                     'atelierelor'],
  'already_resolved_forms': [],
  'already_reserved_forms': [],
  'excluded_form_hypotheses': [],
  'dictionaries': [{'lemma': 'atelier',
                    'url': 'https://dexonline.ro/definitie/atelier/json',
                    'dex_definition_ids': ['830749'],
                    'doom3_definition_ids': ['1324489'],
                    'flexion_url': 'https://dexonline.ro/definitie/atelier',
                    'flexion_authority': 'DOOM3 neuter Atelier '
                                         'table,ateliere/atelierului/atelierelor',
                    'forms_note': 'Six ordinary normalized keys;collective/event senses,vocatives '
                                  'and elisions excluded.',
                    'paraphrase': 'Spațiu dotat pentru muncă meșteșugărească ori '
                                  'industrială,inclusiv secția unei fabrici;nu colectivul sau '
                                  'evenimentul de instruire.; selected DEX sense/register and '
                                  'DOOM3 lexical gender/number checked, ordinary forms from DOOM3 '
                                  'neuter Atelier table,ateliere/atelierului/atelierelor.'}],
  'sources': [{'url': 'https://dexonline.ro/definitie/atelier/json',
               'paraphrase': 'Spațiu dotat pentru muncă meșteșugărească ori industrială,inclusiv '
                             'secția unei fabrici;nu colectivul sau evenimentul de instruire.; '
                             'selected DEX sense/register and DOOM3 lexical gender/number checked, '
                             'ordinary forms from DOOM3 neuter Atelier '
                             'table,ateliere/atelierului/atelierelor.'},
              {'url': 'https://ro.wiktionary.org/wiki/atelier',
               'paraphrase': 'Sensul spațiului de muncă și al secției industriale are paradigma '
                             'ateliere/atelierului/atelierelor.'},
              {'url': 'https://www.rri.ro/rubrici/vizitati-romania/muzeul-satului-isverna-id591495.html',
               'paraphrase': 'Reportajul propriu descrie atelierul fierarului și ciocanul din '
                             'uneltele sale;cache direct de la tick2,reverificat aici.'},
              {'url': 'https://www.roreg.eu/proiecte-de-succes',
               'paraphrase': 'Asociația de dezvoltare descrie un atelier de textile-croitorie '
                             'dotat cu mașini de cusut;se adoptă numai exemplul de dotare.'}],
  'link_targets': [{'node_id': 'n_v4soc_munca',
                    'label': 'muncă',
                    'category': 'societate',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'este un spațiu în care se desfășoară muncă',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_atelier',
                    'edge_dst': 'n_v4soc_munca',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://dexonline.ro/definitie/atelier/json'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v4soc_fabrica',
                    'label': 'fabrică',
                    'category': 'societate',
                    'status': 'main',
                    'relation_hypothesis': 'part_of',
                    'claim_to_verify': 'poate fi o secție a unei fabrici',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_atelier',
                    'edge_dst': 'n_v4soc_fabrica',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://dexonline.ro/definitie/atelier/json'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v32_workshop_hand_ciocan',
                    'label': 'Ciocan',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'un atelier de prelucrare poate folosi ciocane',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_atelier',
                    'edge_dst': 'n_v32_workshop_hand_ciocan',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://www.rri.ro/rubrici/vizitati-romania/muzeul-satului-isverna-id591495.html'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v1_19_masina_de_cusut',
                    'label': 'Mașină de cusut',
                    'category': 'viata_de_roman',
                    'status': 'batch',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'un atelier de croitorie poate folosi mașini de cusut',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_atelier',
                    'edge_dst': 'n_v1_19_masina_de_cusut',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://www.roreg.eu/proiecte-de-succes'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'}],
  'source_acquisition_note': 'ROREG project page fetched directly;RRI tool passage explicitly '
                             'reused. No historical people/place/date/project outcome or '
                             'employment-count facts adopted.',
  'current_graph_counts': {'distinct': 4, 'old_main': 3, 'same_category': 2, 'batch': 1},
  'frequency': {'url': 'https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/ro/ro_50k.txt',
                'best_rank': 9303,
                'matched_form': 'atelier',
                'role': 'Positive signal only; absence does not reject concrete everyday/school '
                        'vocabulary.'},
  'scope': 'Accepted after both once-only independent whole-batch web reviews and explicit verdict '
           'application;reviewed/unapplied/not_landed. No game round,target,recipe,route or '
           'runtime qualification.',
  'review_verdicts': {'factual': {'verdict': 'accept',
                                  'rationale': 'Este spațiul de muncă dotat cu unelte, nu '
                                               'colectivul sau evenimentul; paradigma ateliere '
                                               'este confirmată.'},
                      'quality': {'verdict': 'accept',
                                  'rationale': 'A familiar work space; a real Romanian school '
                                               'textile workshop substantiates the sewing-machine '
                                               'link without implying every workshop contains '
                                               'one.'}}},
 {'id': 'v119-trusa',
  'lemma': 'Trusă',
  'kind': 'new_shared_concept',
  'node_id': 'n_v1_19_trusa',
  'games': ['Cald sau Rece', 'Lanțul Cuvintelor'],
  'sense': 'Ansamblu de instrumente și geanta ori cutia lor,în contextul uneltelor;nu trusă '
           'medicală ca instrucțiune.',
  'register': 'Selected everyday workshop/craft noun sense; unrelated,archaic/poetic-only meanings '
              'excluded;no instructions or clinical ruling.',
  'verified_forms': ['trusă', 'truse', 'trusele', 'trusei', 'truselor'],
  'proposed_forms': ['trusă', 'truse', 'trusele', 'trusei', 'truselor'],
  'already_resolved_forms': [],
  'already_reserved_forms': [],
  'excluded_form_hypotheses': [],
  'dictionaries': [{'lemma': 'trusă',
                    'url': 'https://dexonline.ro/definitie/trus%C4%83/json',
                    'dex_definition_ids': ['836157'],
                    'doom3_definition_ids': ['1270304'],
                    'flexion_url': 'https://dexonline.ro/definitie/trus%C4%83',
                    'flexion_authority': 'DOR feminine Trusă table matching DOOM3 trusei/truse',
                    'forms_note': 'Five ordinary normalized keys;elisions,vocatives and unrelated '
                                  'item families excluded.',
                    'paraphrase': 'Ansamblu de instrumente și geanta ori cutia lor,în contextul '
                                  'uneltelor;nu trusă medicală ca instrucțiune.; selected DEX '
                                  'sense/register and DOOM3 lexical gender/number checked, '
                                  'ordinary forms from DOR feminine Trusă table matching DOOM3 '
                                  'trusei/truse.'}],
  'sources': [{'url': 'https://dexonline.ro/definitie/trus%C4%83/json',
               'paraphrase': 'Ansamblu de instrumente și geanta ori cutia lor,în contextul '
                             'uneltelor;nu trusă medicală ca instrucțiune.; selected DEX '
                             'sense/register and DOOM3 lexical gender/number checked, ordinary '
                             'forms from DOR feminine Trusă table matching DOOM3 trusei/truse.'},
              {'url': 'https://ro.wiktionary.org/wiki/trus%C4%83',
               'paraphrase': 'Trusa poate fi geanta/cutia sau ansamblul de instrumente;paradigma '
                             'truse/trusei/truselor este explicită.'},
              {'url': 'https://www.bosch-diy.com/ro/ro/p/set-de-14-scule-de-man%C4%83-easy-starter-1600a027pt',
               'paraphrase': 'Setul de unelte al producătorului include ciocan,clește și '
                             'șurubelniță într-o geantă;exemplu concret,nu conținut obligatoriu al '
                             'tuturor truselor.'}],
  'link_targets': [{'node_id': 'n_v1_11_cutie',
                    'label': 'Cutie',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'poate păstra uneltele într-o cutie',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_trusa',
                    'edge_dst': 'n_v1_11_cutie',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://dexonline.ro/definitie/trus%C4%83/json'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v32_workshop_hand_ciocan',
                    'label': 'Ciocan',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'o trusă de unelte poate include un ciocan',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_trusa',
                    'edge_dst': 'n_v32_workshop_hand_ciocan',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://www.bosch-diy.com/ro/ro/p/set-de-14-scule-de-man%C4%83-easy-starter-1600a027pt'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v32_workshop_hand_surubelnita',
                    'label': 'Șurubelniță',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'o trusă de unelte poate include o șurubelniță',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_trusa',
                    'edge_dst': 'n_v32_workshop_hand_surubelnita',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://www.bosch-diy.com/ro/ro/p/set-de-14-scule-de-man%C4%83-easy-starter-1600a027pt'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v32_workshop_hand_cleste',
                    'label': 'Clește',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'o trusă de unelte poate include un clește',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_trusa',
                    'edge_dst': 'n_v32_workshop_hand_cleste',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://www.bosch-diy.com/ro/ro/p/set-de-14-scule-de-man%C4%83-easy-starter-1600a027pt'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'}],
  'source_acquisition_note': 'Manufacturer set page fetched directly;its bag example supports tool '
                             'contents,while the optional box caption binds to DEX. No '
                             'dimensions,prices,marketing or practical instructions adopted.',
  'current_graph_counts': {'distinct': 4, 'old_main': 4, 'same_category': 4, 'batch': 0},
  'frequency': {'url': 'https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/ro/ro_50k.txt',
                'best_rank': 17404,
                'matched_form': 'trusă',
                'role': 'Positive signal only; absence does not reject concrete everyday/school '
                        'vocabulary.'},
  'scope': 'Accepted after both once-only independent whole-batch web reviews and explicit verdict '
           'application;reviewed/unapplied/not_landed. No game round,target,recipe,route or '
           'runtime qualification.',
  'review_verdicts': {'factual': {'verdict': 'accept',
                                  'rationale': 'Este ansamblul de instrumente și recipientul lor, '
                                               'cu paradigma truse; un set real confirmă '
                                               'instrumentele numite.'},
                      'quality': {'verdict': 'accept',
                                  'rationale': 'A familiar grouped set/container of tools in '
                                               'school and household catalogues; the description '
                                               'and conditional inventory links are honest.'}}},
 {'id': 'v119-unealta',
  'lemma': 'Unealtă',
  'kind': 'new_shared_concept',
  'node_id': 'n_v1_19_unealta',
  'games': ['Cald sau Rece', 'Lanțul Cuvintelor'],
  'sense': 'Obiect sau dispozitiv folosit pentru o operație practică;nu persoana manipulată sau '
           'instrumentul gramatical.',
  'register': 'Selected everyday workshop/craft noun sense; unrelated,archaic/poetic-only meanings '
              'excluded;no instructions or clinical ruling.',
  'verified_forms': ['unealtă', 'unelte', 'uneltele', 'uneltei', 'uneltelor'],
  'proposed_forms': ['unealtă', 'unelte', 'uneltele', 'uneltei', 'uneltelor'],
  'already_resolved_forms': [],
  'already_reserved_forms': [],
  'excluded_form_hypotheses': [],
  'dictionaries': [{'lemma': 'unealtă',
                    'url': 'https://dexonline.ro/definitie/unealt%C4%83/json',
                    'dex_definition_ids': ['828341'],
                    'doom3_definition_ids': ['1267897'],
                    'flexion_url': 'https://dexonline.ro/definitie/unealt%C4%83',
                    'flexion_authority': 'DOR first physical-tool Unealtă table matching DOOM3 '
                                         'uneltei/unelte',
                    'forms_note': 'Five ordinary normalized keys;figurative/uneltire '
                                  'table,variants,vocatives and elisions excluded.',
                    'paraphrase': 'Obiect sau dispozitiv folosit pentru o operație practică;nu '
                                  'persoana manipulată sau instrumentul gramatical.; selected DEX '
                                  'sense/register and DOOM3 lexical gender/number checked, '
                                  'ordinary forms from DOR first physical-tool Unealtă table '
                                  'matching DOOM3 uneltei/unelte.'}],
  'sources': [{'url': 'https://dexonline.ro/definitie/unealt%C4%83/json',
               'paraphrase': 'Obiect sau dispozitiv folosit pentru o operație practică;nu persoana '
                             'manipulată sau instrumentul gramatical.; selected DEX sense/register '
                             'and DOOM3 lexical gender/number checked, ordinary forms from DOR '
                             'first physical-tool Unealtă table matching DOOM3 uneltei/unelte.'},
              {'url': 'https://ro.wiktionary.org/wiki/unealt%C4%83',
               'paraphrase': 'Sensul de obiect/dispozitiv de lucru și paradigma '
                             'unelte/uneltei/uneltelor sunt explicite.'},
              {'url': 'https://dexonline.ro/definitie/ciocan/json',
               'paraphrase': 'DEX846616,sensul uneltei de lovire,are explicit clasa unealtă.'},
              {'url': 'https://dexonline.ro/definitie/cle%C8%99te/json',
               'paraphrase': 'DEX847600,sensul obiectului de apucat piese,are explicit clasa '
                             'unealtă.'},
              {'url': 'https://dexonline.ro/definitie/%C8%99urubelni%C8%9B%C4%83/json',
               'paraphrase': 'DEX838203 numește șurubelnița unealtă metalică.'},
              {'url': 'https://dexonline.ro/definitie/sap%C4%83/json',
               'paraphrase': 'Sensul agricol al sapei este o unealtă pentru lucrări ale solului.'},
              {'url': 'https://dexonline.ro/definitie/fier%C4%83str%C4%83u/json',
               'paraphrase': 'Sensul de lamă dințată pentru tăiat este o unealtă,nu o expresie '
                             'figurată.'}],
  'link_targets': [{'node_id': 'n_v32_workshop_hand_ciocan',
                    'label': 'Ciocan',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'is_a',
                    'claim_to_verify': 'este o unealtă',
                    'direction': 'incoming',
                    'edge_src': 'n_v32_workshop_hand_ciocan',
                    'edge_dst': 'n_v1_19_unealta',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://dexonline.ro/definitie/unealt%C4%83/json',
                                'https://dexonline.ro/definitie/ciocan/json'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v32_workshop_hand_cleste',
                    'label': 'Clește',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'is_a',
                    'claim_to_verify': 'este o unealtă',
                    'direction': 'incoming',
                    'edge_src': 'n_v32_workshop_hand_cleste',
                    'edge_dst': 'n_v1_19_unealta',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://dexonline.ro/definitie/unealt%C4%83/json',
                                'https://dexonline.ro/definitie/cle%C8%99te/json'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v32_workshop_cut_fierastrau',
                    'label': 'Fierăstrău',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'is_a',
                    'claim_to_verify': 'este o unealtă',
                    'direction': 'incoming',
                    'edge_src': 'n_v32_workshop_cut_fierastrau',
                    'edge_dst': 'n_v1_19_unealta',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://dexonline.ro/definitie/unealt%C4%83/json',
                                'https://dexonline.ro/definitie/fier%C4%83str%C4%83u/json'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v32_workshop_hand_surubelnita',
                    'label': 'Șurubelniță',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'is_a',
                    'claim_to_verify': 'este o unealtă',
                    'direction': 'incoming',
                    'edge_src': 'n_v32_workshop_hand_surubelnita',
                    'edge_dst': 'n_v1_19_unealta',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://dexonline.ro/definitie/unealt%C4%83/json',
                                'https://dexonline.ro/definitie/%C8%99urubelni%C8%9B%C4%83/json'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v1_12_sapa',
                    'label': 'Sapă',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'is_a',
                    'claim_to_verify': 'este o unealtă',
                    'direction': 'incoming',
                    'edge_src': 'n_v1_12_sapa',
                    'edge_dst': 'n_v1_19_unealta',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://dexonline.ro/definitie/unealt%C4%83/json',
                                'https://dexonline.ro/definitie/sap%C4%83/json'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'}],
  'source_acquisition_note': 'Sapă and Fierăstrău JSON fetched only as already-main child-sense '
                             'anchors;no new forms proposed for them here. Other child '
                             'dictionaries are explicit tick1 reuse. Five incoming child→parent '
                             'edges,not reversed parent-is-child captions.',
  'current_graph_counts': {'distinct': 5, 'old_main': 5, 'same_category': 5, 'batch': 0},
  'frequency': {'url': 'https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/ro/ro_50k.txt',
                'best_rank': 10118,
                'matched_form': 'unelte',
                'role': 'Positive signal only; absence does not reject concrete everyday/school '
                        'vocabulary.'},
  'scope': 'Accepted after both once-only independent whole-batch web reviews and explicit verdict '
           'application;reviewed/unapplied/not_landed. No game round,target,recipe,route or '
           'runtime qualification.',
  'review_verdicts': {'factual': {'verdict': 'accept',
                                  'rationale': 'Este dispozitivul fizic de lucru, cu paradigma '
                                               'unelte; sensurile figurat și gramatical rămân '
                                               'excluse.'},
                      'quality': {'verdict': 'accept',
                                  'rationale': 'A basic concrete tool category taught and used '
                                               'broadly; incoming is_a edges classify actual hand '
                                               'tools and approve no puzzle group.'}}},
 {'id': 'v119-masina_de_cusut',
  'lemma': 'Mașină de cusut',
  'kind': 'new_shared_concept',
  'node_id': 'n_v1_19_masina_de_cusut',
  'games': ['Cald sau Rece', 'Lanțul Cuvintelor', 'Conexiuni', 'Intrusul'],
  'sense': 'Mecanism care realizează cusături pe materiale textile;doar sintagma calificată,nu '
           'automobilul sau alte mașini.',
  'register': 'Selected everyday workshop/craft noun sense; unrelated,archaic/poetic-only meanings '
              'excluded;no instructions or clinical ruling.',
  'verified_forms': ['mașină de cusut',
                     'mașini de cusut',
                     'mașinile de cusut',
                     'mașinii de cusut',
                     'mașinilor de cusut'],
  'proposed_forms': ['mașină de cusut',
                     'mașini de cusut',
                     'mașinile de cusut',
                     'mașinii de cusut',
                     'mașinilor de cusut'],
  'already_resolved_forms': [],
  'already_reserved_forms': [],
  'excluded_form_hypotheses': [],
  'dictionaries': [{'lemma': 'mașină',
                    'url': 'https://dexonline.ro/definitie/ma%C8%99in%C4%83/json',
                    'dex_definition_ids': ['886160'],
                    'doom3_definition_ids': ['1291361'],
                    'flexion_url': 'https://dexonline.ro/definitie/ma%C8%99in%C4%83',
                    'flexion_authority': 'DOOM3 feminine Mașină table,mașini/mașinii/mașinilor',
                    'forms_note': 'Five screened qualified normalized keys with invariable de '
                                  'cusut;bare Mașină remains owned by the existing automobile '
                                  'node.',
                    'paraphrase': 'Mecanism care realizează cusături pe materiale textile;doar '
                                  'sintagma calificată,nu automobilul sau alte mașini.; selected '
                                  'DEX sense/register and DOOM3 lexical gender/number checked, '
                                  'ordinary forms from DOOM3 feminine Mașină '
                                  'table,mașini/mașinii/mașinilor.'}],
  'sources': [{'url': 'https://dexonline.ro/definitie/ma%C8%99in%C4%83/json',
               'paraphrase': 'Mecanism care realizează cusături pe materiale textile;doar sintagma '
                             'calificată,nu automobilul sau alte mașini.; selected DEX '
                             'sense/register and DOOM3 lexical gender/number checked, ordinary '
                             'forms from DOOM3 feminine Mașină table,mașini/mașinii/mașinilor.'},
              {'url': 'https://ro.wiktionary.org/wiki/ma%C8%99in%C4%83',
               'paraphrase': 'Sensul de mecanism și paradigma mașini/mașinii/mașinilor susțin '
                             'inflecția capului;toate intrările rămân calificate de cusut.'},
              {'url': 'https://singer-shop.eu/wp-content/uploads/2020/10/manual-Singer-M1500-M1600-converted-min.pdf',
               'paraphrase': 'Manualul propriu SINGER descrie firul/materialul cusut și '
                             'alimentarea electrică a modelului;nu se generalizează alimentarea '
                             'tuturor mașinilor.'},
              {'url': 'https://catalog.manualedigitaleart.ro/art-arte-3-2021/v1/art-arte-3-2021.pdf',
               'paraphrase': 'Lecția Micul croitor,p82,explică realizarea hainelor prin coasere la '
                             'mașină;cache direct de la tick4,reutilizat.'}],
  'link_targets': [{'node_id': 'n_v1_11_ata',
                    'label': 'Ață',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'formează cusături cu ață',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_masina_de_cusut',
                    'edge_dst': 'n_v1_11_ata',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://singer-shop.eu/wp-content/uploads/2020/10/manual-Singer-M1500-M1600-converted-min.pdf'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v29_clothing_everyday_haina',
                    'label': 'Haină',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'poate fi folosită la confecționarea hainelor',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_masina_de_cusut',
                    'edge_dst': 'n_v29_clothing_everyday_haina',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://catalog.manualedigitaleart.ro/art-arte-3-2021/v1/art-arte-3-2021.pdf'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v1_11_panza',
                    'label': 'Pânză',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'poate coase bucăți de pânză',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_masina_de_cusut',
                    'edge_dst': 'n_v1_11_panza',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://singer-shop.eu/wp-content/uploads/2020/10/manual-Singer-M1500-M1600-converted-min.pdf'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v3sti_electricitate',
                    'label': 'Electricitate',
                    'category': 'stiinta',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'modelele electrice folosesc electricitate',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_masina_de_cusut',
                    'edge_dst': 'n_v3sti_electricitate',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://singer-shop.eu/wp-content/uploads/2020/10/manual-Singer-M1500-M1600-converted-min.pdf'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'}],
  'source_acquisition_note': 'Original SINGER manual at distributor fetched directly,text '
                             'extracted in memory;school PDF explicitly reused. Only thread,fabric '
                             'and conditional electric-power facts adopted;no operation or safety '
                             'instructions. Every proposed input retains de cusut qualification.',
  'current_graph_counts': {'distinct': 6, 'old_main': 4, 'same_category': 4, 'batch': 2},
  'frequency': {'url': 'https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/ro/ro_50k.txt',
                'best_rank': None,
                'matched_form': None,
                'role': 'Positive signal only; absence does not reject concrete everyday/school '
                        'vocabulary.'},
  'scope': 'Accepted after both once-only independent whole-batch web reviews and explicit verdict '
           'application;reviewed/unapplied/not_landed. No game round,target,recipe,route or '
           'runtime qualification.',
  'review_verdicts': {'factual': {'verdict': 'accept',
                                  'rationale': 'Sintagma calificată denumește mecanismul textil; '
                                               'flexiunea lui mașină este confirmată și '
                                               'calificativul de cusut rămâne invariabil.'},
                      'quality': {'verdict': 'accept',
                                  'rationale': 'A familiar primary-school and household mechanism; '
                                               'all inputs remain qualified by de cusut and '
                                               'preserve the automobile owner.'}}},
 {'id': 'v119-andrele',
  'lemma': 'Andrele',
  'kind': 'new_shared_concept',
  'node_id': 'n_v1_19_andrele',
  'games': ['Cald sau Rece', 'Lanțul Cuvintelor', 'Conexiuni', 'Intrusul', 'Perechi'],
  'sense': 'Ace lungi și groase pentru tricotatul manual;familia substantivului andrea1,nu '
           'denumirea regională a lunii decembrie.',
  'register': 'Selected everyday workshop/craft noun sense; unrelated,archaic/poetic-only meanings '
              'excluded;no instructions or clinical ruling.',
  'verified_forms': ['andrea', 'andreaua', 'andrele', 'andrelele', 'andrelei', 'andrelelor'],
  'proposed_forms': ['andrea', 'andreaua', 'andrele', 'andrelele', 'andrelei', 'andrelelor'],
  'already_resolved_forms': [],
  'already_reserved_forms': [],
  'excluded_form_hypotheses': [{'form': 'andreei',
                                'reason': 'Ipoteză neconformă cu DOOM3 andrelei pentru acul de '
                                          'tricotat.'},
                               {'form': 'andreii',
                                'reason': 'Ipoteză neconformă cu DOOM3 andrelei pentru acul de '
                                          'tricotat.'}],
  'dictionaries': [{'lemma': 'andrea',
                    'url': 'https://dexonline.ro/definitie/andrea/json',
                    'dex_definition_ids': ['827289'],
                    'doom3_definition_ids': ['1322610'],
                    'flexion_url': 'https://dexonline.ro/definitie/andrea',
                    'flexion_authority': 'DOR first Andrea feminine knitting-needle table matching '
                                         'DOOM3 andrea1',
                    'forms_note': 'Six ordinary normalized keys,including singular '
                                  'andrea/andreaua/andrelei and plural '
                                  'andrele/andrelele/andrelelor;month sense and regional Undrea '
                                  'excluded.',
                    'paraphrase': 'Ace lungi și groase pentru tricotatul manual;familia '
                                  'substantivului andrea1,nu denumirea regională a lunii '
                                  'decembrie.; selected DEX sense/register and DOOM3 lexical '
                                  'gender/number checked, ordinary forms from DOR first Andrea '
                                  'feminine knitting-needle table matching DOOM3 andrea1.'}],
  'sources': [{'url': 'https://dexonline.ro/definitie/andrea/json',
               'paraphrase': 'Ace lungi și groase pentru tricotatul manual;familia substantivului '
                             'andrea1,nu denumirea regională a lunii decembrie.; selected DEX '
                             'sense/register and DOOM3 lexical gender/number checked, ordinary '
                             'forms from DOR first Andrea feminine knitting-needle table matching '
                             'DOOM3 andrea1.'},
              {'url': 'https://ro.wiktionary.org/wiki/andrea',
               'paraphrase': 'Sensul de ace pentru împletit obiecte din lână ori bumbac și '
                             'paradigma andreaua/andrelei/andrele sunt explicite.'},
              {'url': 'https://www.educatieonline.md/Files/Manuals/4/IV_Educatia%20tenhologica%20%28a.%202017%2C%20in%20limba%20romana%29.pdf',
               'paraphrase': 'Capitolul de tricotare descrie firele de lână/bumbac și andrelele '
                             'care formează ochiuri,inclusiv materialul metalic al uneltelor;cache '
                             'direct tick4,reutilizat.'}],
  'link_targets': [{'node_id': 'n_v1_11_lana',
                    'label': 'Lână',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'pot lucra fire din lână',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_andrele',
                    'edge_dst': 'n_v1_11_lana',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://ro.wiktionary.org/wiki/andrea',
                                'https://www.educatieonline.md/Files/Manuals/4/IV_Educatia%20tenhologica%20%28a.%202017%2C%20in%20limba%20romana%29.pdf'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v1_11_ata',
                    'label': 'Ață',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'pot forma ochiuri din ață',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_andrele',
                    'edge_dst': 'n_v1_11_ata',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://www.educatieonline.md/Files/Manuals/4/IV_Educatia%20tenhologica%20%28a.%202017%2C%20in%20limba%20romana%29.pdf'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v1_11_bumbac',
                    'label': 'Bumbac',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'pot lucra fire din bumbac',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_andrele',
                    'edge_dst': 'n_v1_11_bumbac',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://ro.wiktionary.org/wiki/andrea',
                                'https://www.educatieonline.md/Files/Manuals/4/IV_Educatia%20tenhologica%20%28a.%202017%2C%20in%20limba%20romana%29.pdf'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v4sti_metal',
                    'label': 'metal',
                    'category': 'stiinta',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'pot fi fabricate din metal',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_andrele',
                    'edge_dst': 'n_v4sti_metal',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://www.educatieonline.md/Files/Manuals/4/IV_Educatia%20tenhologica%20%28a.%202017%2C%20in%20limba%20romana%29.pdf'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'}],
  'source_acquisition_note': 'Exact dictionary source fetched for Andrea,matching the qualified '
                             'knitting sense;display label remains natural plural Andrele. '
                             'Existing grade4 school PDF explicitly reused and knitting section '
                             'reread;no personal-name or month forms admitted.',
  'current_graph_counts': {'distinct': 4, 'old_main': 4, 'same_category': 3, 'batch': 0},
  'frequency': {'url': 'https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/ro/ro_50k.txt',
                'best_rank': 6072,
                'matched_form': 'andrea',
                'role': 'Positive signal only; absence does not reject concrete everyday/school '
                        'vocabulary.'},
  'scope': 'Accepted after both once-only independent whole-batch web reviews and explicit verdict '
           'application;reviewed/unapplied/not_landed. No game round,target,recipe,route or '
           'runtime qualification.',
  'review_verdicts': {'factual': {'verdict': 'accept',
                                  'rationale': 'Familia feminină andrea1 include singularul și '
                                               'pluralul andrele; luna decembrie și Undrea nu sunt '
                                               'admise.'},
                      'quality': {'verdict': 'accept',
                                  'rationale': 'A familiar primary craft tool, conventionally '
                                               'displayed in the plural; the complete andrea '
                                               'singular/plural family excludes the month and name '
                                               'hypotheses.'}}},
 {'id': 'v119-panglica',
  'lemma': 'Panglică',
  'kind': 'new_shared_concept',
  'node_id': 'n_v1_19_panglica',
  'games': ['Cald sau Rece', 'Lanțul Cuvintelor', 'Conexiuni', 'Intrusul'],
  'sense': 'Fâșie textilă îngustă folosită ca podoabă;nu banda de măsurat,de mașină de '
           'scris,metalul sau sensul zoologic.',
  'register': 'Selected everyday workshop/craft noun sense; unrelated,archaic/poetic-only meanings '
              'excluded;no instructions or clinical ruling.',
  'verified_forms': ['panglică', 'panglici', 'panglicile', 'panglicii', 'panglicilor'],
  'proposed_forms': ['panglică', 'panglici', 'panglicile', 'panglicii', 'panglicilor'],
  'already_resolved_forms': [],
  'already_reserved_forms': [],
  'excluded_form_hypotheses': [],
  'dictionaries': [{'lemma': 'panglică',
                    'url': 'https://dexonline.ro/definitie/panglic%C4%83/json',
                    'dex_definition_ids': ['861038'],
                    'doom3_definition_ids': ['1280204'],
                    'flexion_url': 'https://dexonline.ro/definitie/panglic%C4%83',
                    'flexion_authority': 'DOR feminine Panglică table matching DOOM3 '
                                         'panglicii/panglici',
                    'forms_note': 'Five ordinary normalized keys;regional Pamblică/Pandlică and '
                                  'unrelated senses excluded.',
                    'paraphrase': 'Fâșie textilă îngustă folosită ca podoabă;nu banda de '
                                  'măsurat,de mașină de scris,metalul sau sensul zoologic.; '
                                  'selected DEX sense/register and DOOM3 lexical gender/number '
                                  'checked, ordinary forms from DOR feminine Panglică table '
                                  'matching DOOM3 panglicii/panglici.'}],
  'sources': [{'url': 'https://dexonline.ro/definitie/panglic%C4%83/json',
               'paraphrase': 'Fâșie textilă îngustă folosită ca podoabă;nu banda de măsurat,de '
                             'mașină de scris,metalul sau sensul zoologic.; selected DEX '
                             'sense/register and DOOM3 lexical gender/number checked, ordinary '
                             'forms from DOR feminine Panglică table matching DOOM3 '
                             'panglicii/panglici.'},
              {'url': 'https://ro.wiktionary.org/wiki/panglic%C4%83',
               'paraphrase': 'Sensul decorativ din material textil și paradigma '
                             'panglici/panglicii/panglicilor sunt explicite.'},
              {'url': 'https://www2.hm.com/ro_ro/productpage.1289335001.html',
               'paraphrase': 'Titlul propriu al produsului numește o rochie din satin cu '
                             'panglică;exemplu precis pentru decorarea rochiei.'},
              {'url': 'https://womensecret.com/ro/ro/femeie/accesorii/caciuli/palarie-bej-cu-detalii/6623587.html',
               'paraphrase': 'Descrierea pălăriei numește panglica subțire care o împodobește.'},
              {'url': 'https://www.stoklasa.ro/panglici-din-bumbac-si-panza-x2s011468',
               'paraphrase': 'Merceria comercializează explicit panglici de bumbac/pânză;nu se ia '
                             'sensul diferit de bandă metrică din DEX.'}],
  'link_targets': [{'node_id': 'n_v29_clothing_everyday_haina',
                    'label': 'Haină',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'poate decora o haină',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_panglica',
                    'edge_dst': 'n_v29_clothing_everyday_haina',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://dexonline.ro/definitie/panglic%C4%83/json'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v30_clothing_everyday_rochie',
                    'label': 'Rochie',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'poate decora o rochie',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_panglica',
                    'edge_dst': 'n_v30_clothing_everyday_rochie',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://www2.hm.com/ro_ro/productpage.1289335001.html'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v1_9_palarie',
                    'label': 'Pălărie',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'poate decora o pălărie',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_panglica',
                    'edge_dst': 'n_v1_9_palarie',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://womensecret.com/ro/ro/femeie/accesorii/caciuli/palarie-bej-cu-detalii/6623587.html'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v1_11_panza',
                    'label': 'Pânză',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'poate fi realizată ca o fâșie de pânză',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_panglica',
                    'edge_dst': 'n_v1_11_panza',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://www.stoklasa.ro/panglici-din-bumbac-si-panza-x2s011468'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'}],
  'source_acquisition_note': 'Hat and textile-ribbon sources fetched directly. H&M direct '
                             'request403;full web reader product page opened,title explicitly '
                             'names ribbon-dress. No prices,availability,body/model details or '
                             'garment-care instructions adopted.',
  'current_graph_counts': {'distinct': 4, 'old_main': 4, 'same_category': 4, 'batch': 0},
  'frequency': {'url': 'https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/ro/ro_50k.txt',
                'best_rank': 26936,
                'matched_form': 'panglică',
                'role': 'Positive signal only; absence does not reject concrete everyday/school '
                        'vocabulary.'},
  'scope': 'Accepted after both once-only independent whole-batch web reviews and explicit verdict '
           'application;reviewed/unapplied/not_landed. No game round,target,recipe,route or '
           'runtime qualification.',
  'review_verdicts': {'factual': {'verdict': 'accept',
                                  'rationale': 'Este fâșia textilă decorativă, cu familia '
                                               'panglici/panglicii; sensul zoologic și variantele '
                                               'regionale sunt excluse.'},
                      'quality': {'verdict': 'accept',
                                  'rationale': 'An ordinary decorative textile ribbon, supported '
                                               'by school/craft usage; current indexed '
                                               'clothing/hat examples support the conditional '
                                               'decorations.'}}},
 {'id': 'v119-petic',
  'lemma': 'Petic',
  'kind': 'new_shared_concept',
  'node_id': 'n_v1_19_petic',
  'games': ['Cald sau Rece', 'Lanțul Cuvintelor', 'Conexiuni', 'Intrusul'],
  'sense': 'Bucată de material textil aplicată pentru repararea sau întărirea unei țesături;nu '
           'terenul,metafora sau alt material nespecificat.',
  'register': 'Selected everyday workshop/craft noun sense; unrelated,archaic/poetic-only meanings '
              'excluded;no instructions or clinical ruling.',
  'verified_forms': ['petic', 'peticul', 'petice', 'peticele', 'peticului', 'peticelor'],
  'proposed_forms': ['petic', 'peticul', 'petice', 'peticele', 'peticului', 'peticelor'],
  'already_resolved_forms': [],
  'already_reserved_forms': [],
  'excluded_form_hypotheses': [{'form': 'petec',
                                'reason': 'Unqualified orthographic-variant hypothesis Petec:exact '
                                          'DOOM3 Petec entry missing;complete canonical Petic '
                                          'paradigm retained.'},
                               {'form': 'petecul',
                                'reason': 'Unqualified orthographic-variant hypothesis Petec:exact '
                                          'DOOM3 Petec entry missing;complete canonical Petic '
                                          'paradigm retained.'},
                               {'form': 'petece',
                                'reason': 'Unqualified orthographic-variant hypothesis Petec:exact '
                                          'DOOM3 Petec entry missing;complete canonical Petic '
                                          'paradigm retained.'},
                               {'form': 'petecele',
                                'reason': 'Unqualified orthographic-variant hypothesis Petec:exact '
                                          'DOOM3 Petec entry missing;complete canonical Petic '
                                          'paradigm retained.'},
                               {'form': 'petecului',
                                'reason': 'Unqualified orthographic-variant hypothesis Petec:exact '
                                          'DOOM3 Petec entry missing;complete canonical Petic '
                                          'paradigm retained.'},
                               {'form': 'petecelor',
                                'reason': 'Unqualified orthographic-variant hypothesis Petec:exact '
                                          'DOOM3 Petec entry missing;complete canonical Petic '
                                          'paradigm retained.'}],
  'excluded_lexeme_hypotheses': [{'lemma': 'Petec',
                                  'forms': [],
                                  'role': 'orthographic_variant_hypothesis',
                                  'status': 'unresearched_hypothesis_only',
                                  'pre_screened_form_hypotheses': ['petec',
                                                                   'petecul',
                                                                   'petece',
                                                                   'petecele',
                                                                   'petecului',
                                                                   'petecelor'],
                                  'decision': 'held component:exact Petec DOOM3 entry missing;no '
                                              'input admitted'}],
  'dictionaries': [{'lemma': 'petic',
                    'url': 'https://dexonline.ro/definitie/petic/json',
                    'dex_definition_ids': ['870959'],
                    'doom3_definition_ids': ['1282202'],
                    'flexion_url': 'https://dexonline.ro/definitie/petic',
                    'flexion_authority': 'DOR canonical neuter Petic table matching DOOM3 petice',
                    'forms_note': 'Six complete canonical normalized keys;all six Petec-variant '
                                  'hypotheses excluded for absent exact normative headword,not '
                                  'partial canonical inflection.',
                    'paraphrase': 'Bucată de material textil aplicată pentru repararea sau '
                                  'întărirea unei țesături;nu terenul,metafora sau alt material '
                                  'nespecificat.; selected DEX sense/register and DOOM3 lexical '
                                  'gender/number checked, ordinary forms from DOR canonical neuter '
                                  'Petic table matching DOOM3 petice.'}],
  'sources': [{'url': 'https://dexonline.ro/definitie/petic/json',
               'paraphrase': 'Bucată de material textil aplicată pentru repararea sau întărirea '
                             'unei țesături;nu terenul,metafora sau alt material nespecificat.; '
                             'selected DEX sense/register and DOOM3 lexical gender/number checked, '
                             'ordinary forms from DOR canonical neuter Petic table matching DOOM3 '
                             'petice.'},
              {'url': 'https://ro.wiktionary.org/wiki/petic',
               'paraphrase': 'Sensul de bucată textilă pentru reparare și paradigma '
                             'petice/peticului/peticelor sunt explicite.'},
              {'url': 'https://www.stoklasa.ro/petice-termoadezive-imitatie-piele-intoarsa-x147090',
               'paraphrase': 'Produsul propriu este un petic pentru haine și pantaloni,cu '
                             'posibilitate de coasere;compoziția imprecisă a paginii nu este '
                             'adoptată.'},
              {'url': 'https://dexonline.ro/definitie/coase/json',
               'paraphrase': 'DEX definește coaserea prin ac și ață,calificând explicit firul '
                             'pentru fixarea unui petic cusut.'}],
  'link_targets': [{'node_id': 'n_v1_11_panza',
                    'label': 'Pânză',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'poate fi o bucată de pânză',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_petic',
                    'edge_dst': 'n_v1_11_panza',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://dexonline.ro/definitie/petic/json'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v29_clothing_everyday_haina',
                    'label': 'Haină',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'poate repara o parte ruptă din haină',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_petic',
                    'edge_dst': 'n_v29_clothing_everyday_haina',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://dexonline.ro/definitie/petic/json',
                                'https://www.stoklasa.ro/petice-termoadezive-imitatie-piele-intoarsa-x147090'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v30_clothing_everyday_pantaloni',
                    'label': 'Pantaloni',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'poate întări o parte a pantalonilor',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_petic',
                    'edge_dst': 'n_v30_clothing_everyday_pantaloni',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://www.stoklasa.ro/petice-termoadezive-imitatie-piele-intoarsa-x147090'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v1_11_ata',
                    'label': 'Ață',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'poate fi prins prin coasere cu ață',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_petic',
                    'edge_dst': 'n_v1_11_ata',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://dexonline.ro/definitie/petic/json',
                                'https://www.stoklasa.ro/petice-termoadezive-imitatie-piele-intoarsa-x147090',
                                'https://dexonline.ro/definitie/coase/json'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'}],
  'source_acquisition_note': 'Product and Coase DEX anchor fetched directly. Canonical Petic exact '
                             'norm retained in full;Petec auxiliary variant excluded in full with '
                             'observed evidence preserved. Pants repair is the explicit '
                             'combination of generic textile-repair definition and actual '
                             'trouser-patch use,not a quotation or new endpoint. No product '
                             'composition,quantities or instructions adopted.',
  'current_graph_counts': {'distinct': 4, 'old_main': 4, 'same_category': 4, 'batch': 0},
  'frequency': {'url': 'https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/ro/ro_50k.txt',
                'best_rank': 34576,
                'matched_form': 'petic',
                'role': 'Positive signal only; absence does not reject concrete everyday/school '
                        'vocabulary.'},
  'scope': 'Accepted after both once-only independent whole-batch web reviews and explicit verdict '
           'application;reviewed/unapplied/not_landed. No game round,target,recipe,route or '
           'runtime qualification.',
  'review_corrections': [{'kind': 'replace_edge_caption',
                          'src': 'n_v1_19_petic',
                          'dst': 'n_v30_clothing_everyday_pantaloni',
                          'relation': 'related_to',
                          'before': 'poate acoperi o ruptură în pantaloni',
                          'after': 'poate întări o parte a pantalonilor',
                          'reviewers': ['quality']}],
  'fresh_review_source_binding_notes': ['The exact correction above supplies the current reviewed '
                                        'edge authority; earlier acquisition notes describe '
                                        'historical author research and do not override the fresh '
                                        'binding.'],
  'review_verdicts': {'factual': {'verdict': 'accept',
                                  'rationale': 'Este bucata de material pentru repararea hainei; '
                                               'familia petice este completă și întreaga familie '
                                               'Petec rămâne exclusă.'},
                      'quality': {'verdict': 'modify',
                                  'rationale': 'A familiar textile repair patch; retain the '
                                               'complete Petic family and excluded Petec family, '
                                               'but narrow the trousers caption to the sourced '
                                               'reinforcement use.'}}},
 {'id': 'v119-cusatura',
  'lemma': 'Cusătură',
  'kind': 'new_shared_concept',
  'node_id': 'n_v1_19_cusatura',
  'games': ['Cald sau Rece', 'Lanțul Cuvintelor'],
  'sense': 'Îmbinare realizată cu ață între bucăți de material textil;nu acțiunea,plaga sau '
           'îmbinarea metalică.',
  'register': 'Selected everyday workshop/craft noun sense; unrelated,archaic/poetic-only meanings '
              'excluded;no instructions or clinical ruling.',
  'verified_forms': ['cusătură', 'cusături', 'cusăturile', 'cusăturii', 'cusăturilor'],
  'proposed_forms': ['cusătură', 'cusături', 'cusăturile', 'cusăturii', 'cusăturilor'],
  'already_resolved_forms': [],
  'already_reserved_forms': [],
  'excluded_form_hypotheses': [],
  'dictionaries': [{'lemma': 'cusătură',
                    'url': 'https://dexonline.ro/definitie/cus%C4%83tur%C4%83/json',
                    'dex_definition_ids': ['855058'],
                    'doom3_definition_ids': ['1316654'],
                    'flexion_url': 'https://dexonline.ro/definitie/cus%C4%83tur%C4%83',
                    'flexion_authority': 'DOR feminine Cusătură table matching DOOM3 '
                                         'cusăturii/cusături',
                    'forms_note': 'Five ordinary normalized keys;medical,metallic,action senses '
                                  'and regional Cusutură excluded.',
                    'paraphrase': 'Îmbinare realizată cu ață între bucăți de material textil;nu '
                                  'acțiunea,plaga sau îmbinarea metalică.; selected DEX '
                                  'sense/register and DOOM3 lexical gender/number checked, '
                                  'ordinary forms from DOR feminine Cusătură table matching DOOM3 '
                                  'cusăturii/cusături.'}],
  'sources': [{'url': 'https://dexonline.ro/definitie/cus%C4%83tur%C4%83/json',
               'paraphrase': 'Îmbinare realizată cu ață între bucăți de material textil;nu '
                             'acțiunea,plaga sau îmbinarea metalică.; selected DEX sense/register '
                             'and DOOM3 lexical gender/number checked, ordinary forms from DOR '
                             'feminine Cusătură table matching DOOM3 cusăturii/cusături.'},
              {'url': 'https://ro.wiktionary.org/wiki/cus%C4%83tur%C4%83',
               'paraphrase': 'Sensul de îmbinare a pânzei și ața cusută are paradigma '
                             'cusături/cusăturii/cusăturilor.'},
              {'url': 'https://singer-shop.eu/wp-content/uploads/2020/10/manual-Singer-M1500-M1600-converted-min.pdf',
               'paraphrase': 'Manualul propriu mașinii de cusut descrie cusătura dreaptă și alte '
                             'cusături;cache direct din acest tick,reutilizat.'},
              {'url': 'https://dexonline.ro/definitie/coase/json',
               'paraphrase': 'DEX848131,sensul1,leagă prin ac și ață părțile unei haine;cache '
                             'direct de la Petic,reutilizat.'},
              {'url': 'https://catalog.manualedigitaleart.ro/art-arte-3-2021/v1/art-arte-3-2021.pdf',
               'paraphrase': 'Lecția primară Micul croitor,p82,descrie coaserea părților croite '
                             'ale unei haine;cache tick4,reutilizat.'}],
  'link_targets': [{'node_id': 'n_v1_11_ata',
                    'label': 'Ață',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'se poate realiza cu ață',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_cusatura',
                    'edge_dst': 'n_v1_11_ata',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://dexonline.ro/definitie/cus%C4%83tur%C4%83/json'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v1_11_panza',
                    'label': 'Pânză',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'poate uni bucăți de pânză',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_cusatura',
                    'edge_dst': 'n_v1_11_panza',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://dexonline.ro/definitie/cus%C4%83tur%C4%83/json'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v29_clothing_everyday_haina',
                    'label': 'Haină',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'part_of',
                    'claim_to_verify': 'poate uni părți ale unei haine',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_cusatura',
                    'edge_dst': 'n_v29_clothing_everyday_haina',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://dexonline.ro/definitie/coase/json',
                                'https://catalog.manualedigitaleart.ro/art-arte-3-2021/v1/art-arte-3-2021.pdf'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v1_19_masina_de_cusut',
                    'label': 'Mașină de cusut',
                    'category': 'viata_de_roman',
                    'status': 'batch',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'se poate realiza cu mașina de cusut',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_cusatura',
                    'edge_dst': 'n_v1_19_masina_de_cusut',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://singer-shop.eu/wp-content/uploads/2020/10/manual-Singer-M1500-M1600-converted-min.pdf'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'}],
  'source_acquisition_note': 'All non-current sources explicitly reused from direct acquisitions '
                             'within tick5 or tick4 and relevant passages reread;no fresh download '
                             'claimed. Textile joint only;no surgical fact or instructions '
                             'adopted.',
  'current_graph_counts': {'distinct': 5, 'old_main': 3, 'same_category': 5, 'batch': 2},
  'frequency': {'url': 'https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/ro/ro_50k.txt',
                'best_rank': 32098,
                'matched_form': 'cusături',
                'role': 'Positive signal only; absence does not reject concrete everyday/school '
                        'vocabulary.'},
  'scope': 'Accepted after both once-only independent whole-batch web reviews and explicit verdict '
           'application;reviewed/unapplied/not_landed. No game round,target,recipe,route or '
           'runtime qualification.',
  'review_verdicts': {'factual': {'verdict': 'accept',
                                  'rationale': 'Este îmbinarea textilă, cu familia '
                                               'cusături/cusăturii; sensurile medical și metalic '
                                               'sunt excluse.'},
                      'quality': {'verdict': 'accept',
                                  'rationale': 'An explicitly taught primary-school textile join, '
                                               'with household-machine evidence; medical and '
                                               'metallic joins are excluded.'}}},
 {'id': 'v119-tiv',
  'lemma': 'Tiv',
  'kind': 'new_shared_concept',
  'node_id': 'n_v1_19_tiv',
  'games': ['Cald sau Rece', 'Lanțul Cuvintelor'],
  'sense': 'Margine textilă îndoită și cusută,pentru finisarea obiectului;nu metafora literară '
           'despre nori sau acoperișuri.',
  'register': 'Selected everyday workshop/craft noun sense; unrelated,archaic/poetic-only meanings '
              'excluded;no instructions or clinical ruling.',
  'verified_forms': ['tiv', 'tivul', 'tivuri', 'tivurile', 'tivului', 'tivurilor'],
  'proposed_forms': ['tiv', 'tivul', 'tivuri', 'tivurile', 'tivului', 'tivurilor'],
  'already_resolved_forms': [],
  'already_reserved_forms': [],
  'excluded_form_hypotheses': [],
  'dictionaries': [{'lemma': 'tiv',
                    'url': 'https://dexonline.ro/definitie/tiv/json',
                    'dex_definition_ids': ['833743'],
                    'doom3_definition_ids': ['1268941'],
                    'flexion_url': 'https://dexonline.ro/definitie/tiv',
                    'flexion_authority': 'DOR neuter Tiv table matching DOOM3 tivuri',
                    'forms_note': 'Six ordinary normalized keys;vocatives,elisions and figurative '
                                  'literary meanings excluded.',
                    'paraphrase': 'Margine textilă îndoită și cusută,pentru finisarea '
                                  'obiectului;nu metafora literară despre nori sau acoperișuri.; '
                                  'selected DEX sense/register and DOOM3 lexical gender/number '
                                  'checked, ordinary forms from DOR neuter Tiv table matching '
                                  'DOOM3 tivuri.'}],
  'sources': [{'url': 'https://dexonline.ro/definitie/tiv/json',
               'paraphrase': 'Margine textilă îndoită și cusută,pentru finisarea obiectului;nu '
                             'metafora literară despre nori sau acoperișuri.; selected DEX '
                             'sense/register and DOOM3 lexical gender/number checked, ordinary '
                             'forms from DOR neuter Tiv table matching DOOM3 tivuri.'},
              {'url': 'https://ro.wiktionary.org/wiki/tiv',
               'paraphrase': 'Sensul de margine textilă fixată prin cusătură și paradigma '
                             'tivuri/tivului/tivurilor sunt explicite.'},
              {'url': 'https://singer-shop.eu/wp-content/uploads/2020/10/manual-Singer-M1500-M1600-converted-min.pdf',
               'paraphrase': 'Manualul SINGER numește explicit tivuri pentru pantaloni;cache '
                             'direct din acest tick,reutilizat.'},
              {'url': 'https://minervapatterns.com/model/5682?lang=ro',
               'paraphrase': 'Tiparul propriu de rochie descrie tivul rochiei îndoit și cusut;se '
                             'adoptă numai relația de finisare,nu instrucțiunile.'},
              {'url': 'https://dexonline.ro/definitie/coase/json',
               'paraphrase': 'Definiția coaserii include firul de ață;susține firul folosit la '
                             'fixarea unui tiv cusut.'}],
  'link_targets': [{'node_id': 'n_v1_19_cusatura',
                    'label': 'Cusătură',
                    'category': 'viata_de_roman',
                    'status': 'batch',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'poate fi fixat prin cusătură',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_tiv',
                    'edge_dst': 'n_v1_19_cusatura',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://dexonline.ro/definitie/tiv/json'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v30_clothing_everyday_rochie',
                    'label': 'Rochie',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'part_of',
                    'claim_to_verify': 'poate finisa marginea unei rochii',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_tiv',
                    'edge_dst': 'n_v30_clothing_everyday_rochie',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://minervapatterns.com/model/5682?lang=ro'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v30_clothing_everyday_pantaloni',
                    'label': 'Pantaloni',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'part_of',
                    'claim_to_verify': 'poate finisa marginea pantalonilor',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_tiv',
                    'edge_dst': 'n_v30_clothing_everyday_pantaloni',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://singer-shop.eu/wp-content/uploads/2020/10/manual-Singer-M1500-M1600-converted-min.pdf'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v1_11_ata',
                    'label': 'Ață',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'poate fi fixat prin coasere cu ață',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_tiv',
                    'edge_dst': 'n_v1_11_ata',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://dexonline.ro/definitie/tiv/json',
                                'https://dexonline.ro/definitie/coase/json'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'}],
  'source_acquisition_note': 'Romanian-language original dress pattern fetched '
                             'directly;manufacturer manual and Coase definition explicitly reused '
                             'from this tick. No dimensions,instruction steps or fashion claims '
                             'adopted.',
  'current_graph_counts': {'distinct': 4, 'old_main': 3, 'same_category': 4, 'batch': 1},
  'frequency': {'url': 'https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/ro/ro_50k.txt',
                'best_rank': None,
                'matched_form': None,
                'role': 'Positive signal only; absence does not reject concrete everyday/school '
                        'vocabulary.'},
  'scope': 'Accepted after both once-only independent whole-batch web reviews and explicit verdict '
           'application;reviewed/unapplied/not_landed. No game round,target,recipe,route or '
           'runtime qualification.',
  'review_verdicts': {'factual': {'verdict': 'accept',
                                  'rationale': 'Este marginea textilă îndoită și cusută, cu '
                                               'paradigma neutră tivuri; exemplele de rochie și '
                                               'pantaloni sunt confirmate.'},
                      'quality': {'verdict': 'accept',
                                  'rationale': 'An everyday garment edge with concrete Romanian '
                                               'sewing examples for trousers and dresses; no '
                                               'literary metaphor is needed.'}}},
 {'id': 'v119-broderie',
  'lemma': 'Broderie',
  'kind': 'new_shared_concept',
  'node_id': 'n_v1_19_broderie',
  'games': ['Cald sau Rece', 'Lanțul Cuvintelor'],
  'sense': 'Ornament realizat prin coasere cu fire pe material textil;nu nota muzicală sau '
           'ornamentația metaforică.',
  'register': 'Selected everyday workshop/craft noun sense; unrelated,archaic/poetic-only meanings '
              'excluded;no instructions or clinical ruling.',
  'verified_forms': ['broderie', 'broderia', 'broderii', 'broderiile', 'broderiei', 'broderiilor'],
  'proposed_forms': ['broderie', 'broderia', 'broderii', 'broderiile', 'broderiei', 'broderiilor'],
  'already_resolved_forms': [],
  'already_reserved_forms': [],
  'excluded_form_hypotheses': [],
  'dictionaries': [{'lemma': 'broderie',
                    'url': 'https://dexonline.ro/definitie/broderie/json',
                    'dex_definition_ids': ['837358'],
                    'doom3_definition_ids': ['1319569'],
                    'flexion_url': 'https://dexonline.ro/definitie/broderie',
                    'flexion_authority': 'DOOM3 feminine Broderie '
                                         'table,broderia/broderiei/broderii/broderiile',
                    'forms_note': 'Six ordinary normalized keys;Brodărie variant,musical and '
                                  'figurative meanings excluded.',
                    'paraphrase': 'Ornament realizat prin coasere cu fire pe material textil;nu '
                                  'nota muzicală sau ornamentația metaforică.; selected DEX '
                                  'sense/register and DOOM3 lexical gender/number checked, '
                                  'ordinary forms from DOOM3 feminine Broderie '
                                  'table,broderia/broderiei/broderii/broderiile.'}],
  'sources': [{'url': 'https://dexonline.ro/definitie/broderie/json',
               'paraphrase': 'Ornament realizat prin coasere cu fire pe material textil;nu nota '
                             'muzicală sau ornamentația metaforică.; selected DEX sense/register '
                             'and DOOM3 lexical gender/number checked, ordinary forms from DOOM3 '
                             'feminine Broderie table,broderia/broderiei/broderii/broderiile.'},
              {'url': 'https://ro.wiktionary.org/wiki/broderie',
               'paraphrase': 'Sensul textilei decorate prin cusătură și paradigma '
                             'broderii/broderiei/broderiilor sunt explicite.'},
              {'url': 'https://www.educatieonline.md/Files/Manuals/4/IV_Educatia%20tenhologica%20%28a.%202017%2C%20in%20limba%20romana%29.pdf',
               'paraphrase': 'Capitolul de brodat descrie pânza și firele textile pentru '
                             'broderie;cache direct tick4,reutilizat.'},
              {'url': 'https://ienationala.ro/products/rochie-traditionala-tip-ie-brodata-adina-negru-03?variant=55484644688214',
               'paraphrase': 'Produsul propriu al atelierului este o rochie cu broderie '
                             'geometrică,exemplu concret de ornament al unei haine.'},
              {'url': 'https://dexonline.ro/definitie/coase/json',
               'paraphrase': 'DEX848131 leagă coaserea de firul de ață și include brodarea;cache '
                             'direct din acest tick,reutilizat.'}],
  'link_targets': [{'node_id': 'n_v1_11_ata',
                    'label': 'Ață',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'poate fi realizată cu ață pentru modele decorative',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_broderie',
                    'edge_dst': 'n_v1_11_ata',
                    'verdict': 'accepted_reviewed_unapplied',
                    'original_claim_hypothesis': 'poate realiza modele decorative cu ață',
                    'sources': ['https://www.educatieonline.md/Files/Manuals/4/IV_Educatia%20tenhologica%20%28a.%202017%2C%20in%20limba%20romana%29.pdf',
                                'https://dexonline.ro/definitie/broderie/json',
                                'https://dexonline.ro/definitie/coase/json'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v1_11_panza',
                    'label': 'Pânză',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'poate decora pânza',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_broderie',
                    'edge_dst': 'n_v1_11_panza',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://www.educatieonline.md/Files/Manuals/4/IV_Educatia%20tenhologica%20%28a.%202017%2C%20in%20limba%20romana%29.pdf',
                                'https://dexonline.ro/definitie/broderie/json'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v29_clothing_everyday_haina',
                    'label': 'Haină',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'poate decora o haină',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_broderie',
                    'edge_dst': 'n_v29_clothing_everyday_haina',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://ienationala.ro/products/rochie-traditionala-tip-ie-brodata-adina-negru-03?variant=55484644688214'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'},
                   {'node_id': 'n_v30_clothing_everyday_rochie',
                    'label': 'Rochie',
                    'category': 'viata_de_roman',
                    'status': 'main',
                    'relation_hypothesis': 'related_to',
                    'claim_to_verify': 'poate decora o rochie',
                    'direction': 'outgoing',
                    'edge_src': 'n_v1_19_broderie',
                    'edge_dst': 'n_v30_clothing_everyday_rochie',
                    'verdict': 'accepted_reviewed_unapplied',
                    'sources': ['https://ienationala.ro/products/rochie-traditionala-tip-ie-brodata-adina-negru-03?variant=55484644688214'],
                    'evidence_note': 'Both independent whole-batch web reviews completed;required '
                                     'corrections applied to this source proposal. No runtime '
                                     'application.'}],
  'source_acquisition_note': 'First-party embroidered-dress page fetched directly;school textile '
                             'chapter and Coase DEX anchor explicitly reused. Passive thread '
                             'caption matches the selected ornament sense;no claim that an object '
                             'itself performs embroidery. No textile history,ethnicity '
                             'attribution,prices or instructions adopted.',
  'current_graph_counts': {'distinct': 4, 'old_main': 4, 'same_category': 4, 'batch': 0},
  'frequency': {'url': 'https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/ro/ro_50k.txt',
                'best_rank': None,
                'matched_form': None,
                'role': 'Positive signal only; absence does not reject concrete everyday/school '
                        'vocabulary.'},
  'scope': 'Accepted after both once-only independent whole-batch web reviews and explicit verdict '
           'application;reviewed/unapplied/not_landed. No game round,target,recipe,route or '
           'runtime qualification.',
  'review_verdicts': {'factual': {'verdict': 'accept',
                                  'rationale': 'Este ornamentul textil cusut, cu familia '
                                               'broderia/broderiei/broderii; sensurile muzical și '
                                               'figurat sunt excluse.'},
                      'quality': {'verdict': 'accept',
                                  'rationale': 'Primary-school and current Romanian clothing '
                                               'evidence support the decorative sewn ornament; '
                                               'musical/figurative senses are excluded.'}}},
 {'id': 'v119-ciocan',
  'lemma': 'Ciocan',
  'kind': 'existing_input_family',
  'node_id': 'n_v32_workshop_hand_ciocan',
  'games': ['Cald sau Rece', 'Lanțul Cuvintelor'],
  'sense': 'Unealta manuală de lovire din nodul servit;excluse osul,păhărelul și știuletele '
           'regional.',
  'register': 'Selected everyday workshop/craft noun sense; unrelated,archaic/poetic-only meanings '
              'excluded;no instructions or clinical ruling.',
  'verified_forms': ['ciocan', 'ciocanul', 'ciocane', 'ciocanele', 'ciocanului', 'ciocanelor'],
  'proposed_forms': ['ciocanelor'],
  'already_resolved_forms': ['ciocan', 'ciocanul', 'ciocane', 'ciocanele', 'ciocanului'],
  'already_reserved_forms': [],
  'excluded_form_hypotheses': [],
  'dictionaries': [{'lemma': 'ciocan',
                    'url': 'https://dexonline.ro/definitie/ciocan/json',
                    'dex_definition_ids': ['846616'],
                    'doom3_definition_ids': ['1311742'],
                    'flexion_url': 'https://dexonline.ro/definitie/ciocan',
                    'flexion_authority': 'DOOM3 ciocan2 (unealtă) neuter;explicit DOR N1 table '
                                         'labeled ciocan (unealtă),not masculine știulete/cotor',
                    'forms_note': 'ciocan/ciocanul/ciocane/ciocanele/ciocanului/ciocanelor;no '
                                  'ciocani,elisions or vocatives.',
                    'paraphrase': 'Unealta manuală de lovire din nodul servit;excluse '
                                  'osul,păhărelul și știuletele regional.; selected DEX '
                                  'sense/register and DOOM3 lexical gender/number checked, '
                                  'ordinary forms from DOOM3 ciocan2 (unealtă) neuter;explicit DOR '
                                  'N1 table labeled ciocan (unealtă),not masculine '
                                  'știulete/cotor.'}],
  'sources': [{'url': 'https://dexonline.ro/definitie/ciocan/json',
               'paraphrase': 'Unealta manuală de lovire din nodul servit;excluse osul,păhărelul și '
                             'știuletele regional.; selected DEX sense/register and DOOM3 lexical '
                             'gender/number checked, ordinary forms from DOOM3 ciocan2 (unealtă) '
                             'neuter;explicit DOR N1 table labeled ciocan (unealtă),not masculine '
                             'știulete/cotor.'},
              {'url': 'https://ro.wiktionary.org/wiki/ciocan',
               'paraphrase': 'Secțiunea neutră pentru unealta de lovire confirmă '
                             'ciocanelor;secțiunea masculină și sensurile de pahar/os nu sunt '
                             'selectate.'}],
  'link_targets': [],
  'existing_sense_restriction': 'Same existing tool owner n_v32_workshop_hand_ciocan;grammatical '
                                'completion only,not a synonym.',
  'frequency': {'url': 'https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/ro/ro_50k.txt',
                'best_rank': 8780,
                'matched_form': 'ciocan',
                'role': 'Positive signal only; absence does not reject concrete everyday/school '
                        'vocabulary.'},
  'scope': 'Accepted after both once-only independent whole-batch web reviews and explicit verdict '
           'application;reviewed/unapplied/not_landed. No game round,target,recipe,route or '
           'runtime qualification.',
  'review_verdicts': {'factual': {'verdict': 'accept',
                                  'rationale': 'Este familia neutră a uneltei de lovire; numai '
                                               'cheia lipsă ciocanelor completează nodul existent, '
                                               'fără alte sensuri.'},
                      'quality': {'verdict': 'accept',
                                  'rationale': 'The existing familiar hand-hammer owner receives '
                                               'only its missing canonical genitive plural; other '
                                               'senses and masculine ciocani stay excluded.'}}},
 {'id': 'v119-surub',
  'lemma': 'Șurub',
  'kind': 'existing_input_family',
  'node_id': 'n_v32_workshop_fastener_surub',
  'games': ['Cald sau Rece', 'Lanțul Cuvintelor'],
  'sense': 'Piesa filetată de fixare din nodul servit;excluse sensurile figurate și dispozitivele '
           'numite prin extensie.',
  'register': 'Selected everyday workshop/craft noun sense; unrelated,archaic/poetic-only meanings '
              'excluded;no instructions or clinical ruling.',
  'verified_forms': ['șurub', 'șurubul', 'șuruburi', 'șuruburile', 'șurubului', 'șuruburilor'],
  'proposed_forms': ['șuruburilor'],
  'already_resolved_forms': ['șurub', 'șurubul', 'șuruburi', 'șuruburile', 'șurubului'],
  'already_reserved_forms': [],
  'excluded_form_hypotheses': [],
  'dictionaries': [{'lemma': 'șurub',
                    'url': 'https://dexonline.ro/definitie/%C8%99urub/json',
                    'dex_definition_ids': ['838198'],
                    'doom3_definition_ids': ['1271960'],
                    'flexion_url': 'https://dexonline.ro/definitie/%C8%99urub',
                    'flexion_authority': 'DOOM3 neuter șurub/șuruburi plus first matching DOR '
                                         'table,not șurup variant table',
                    'forms_note': 'șurub/șurubul/șuruburi/șuruburile/șurubului/șuruburilor;no '
                                  'regional variants,elisions or vocatives.',
                    'paraphrase': 'Piesa filetată de fixare din nodul servit;excluse sensurile '
                                  'figurate și dispozitivele numite prin extensie.; selected DEX '
                                  'sense/register and DOOM3 lexical gender/number checked, '
                                  'ordinary forms from DOOM3 neuter șurub/șuruburi plus first '
                                  'matching DOR table,not șurup variant table.'}],
  'sources': [{'url': 'https://dexonline.ro/definitie/%C8%99urub/json',
               'paraphrase': 'Piesa filetată de fixare din nodul servit;excluse sensurile figurate '
                             'și dispozitivele numite prin extensie.; selected DEX sense/register '
                             'and DOOM3 lexical gender/number checked, ordinary forms from DOOM3 '
                             'neuter șurub/șuruburi plus first matching DOR table,not șurup '
                             'variant table.'},
              {'url': 'https://ro.wiktionary.org/wiki/%C8%99urub',
               'paraphrase': 'Confirmă tija filetată pentru asamblare și genitivul plural '
                             'șuruburilor;nu sunt selectate variantele regionale sau sensurile '
                             'figurate.'}],
  'link_targets': [],
  'existing_sense_restriction': 'Same existing threaded-fastener owner '
                                'n_v32_workshop_fastener_surub;grammatical completion only,not a '
                                'synonym.',
  'frequency': {'url': 'https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/ro/ro_50k.txt',
                'best_rank': 25615,
                'matched_form': 'șurub',
                'role': 'Positive signal only; absence does not reject concrete everyday/school '
                        'vocabulary.'},
  'scope': 'Accepted after both once-only independent whole-batch web reviews and explicit verdict '
           'application;reviewed/unapplied/not_landed. No game round,target,recipe,route or '
           'runtime qualification.',
  'review_verdicts': {'factual': {'verdict': 'accept',
                                  'rationale': 'Este familia neutră a piesei filetate; numai cheia '
                                               'lipsă șuruburilor completează proprietarul '
                                               'existent.'},
                      'quality': {'verdict': 'accept',
                                  'rationale': 'The existing familiar threaded-fastener owner '
                                               'receives only its missing canonical genitive '
                                               'plural; existing qualified resolutions are '
                                               'preserved.'}}},
 {'id': 'v119-fierastrau',
  'lemma': 'Fierăstrău',
  'kind': 'existing_input_family',
  'node_id': 'n_v32_workshop_cut_fierastrau',
  'games': ['Cald sau Rece', 'Lanțul Cuvintelor'],
  'sense': 'Unealtă sau mașină-unealtă cu lamă dințată pentru tăiere;familie de intrări a nodului '
           'existent,nu instrumentul muzical.',
  'register': 'Selected everyday workshop/craft noun sense; unrelated,archaic/poetic-only meanings '
              'excluded;no instructions or clinical ruling.',
  'verified_forms': ['fierăstrău',
                     'fierăstrăul',
                     'fierăstraie',
                     'fierăstraiele',
                     'fierăstrăului',
                     'fierăstraielor'],
  'proposed_forms': ['fierăstraielor'],
  'already_resolved_forms': ['fierăstrău',
                             'fierăstrăul',
                             'fierăstraie',
                             'fierăstraiele',
                             'fierăstrăului'],
  'already_reserved_forms': [],
  'excluded_form_hypotheses': [{'form': 'ferăstrău',
                                'reason': 'Older Ferăstrău spelling/table is DOOM2 only;no exact '
                                          'current DOOM3 entry;native existing resolutions '
                                          'unchanged.'},
                               {'form': 'ferăstrăul',
                                'reason': 'Older Ferăstrău spelling/table is DOOM2 only;no exact '
                                          'current DOOM3 entry;native existing resolutions '
                                          'unchanged.'},
                               {'form': 'ferăstraie',
                                'reason': 'Older Ferăstrău spelling/table is DOOM2 only;no exact '
                                          'current DOOM3 entry;native existing resolutions '
                                          'unchanged.'},
                               {'form': 'ferăstraiele',
                                'reason': 'Older Ferăstrău spelling/table is DOOM2 only;no exact '
                                          'current DOOM3 entry;native existing resolutions '
                                          'unchanged.'},
                               {'form': 'ferăstrăului',
                                'reason': 'Older Ferăstrău spelling/table is DOOM2 only;no exact '
                                          'current DOOM3 entry;native existing resolutions '
                                          'unchanged.'},
                               {'form': 'ferăstraielor',
                                'reason': 'Older Ferăstrău spelling/table is DOOM2 only;no exact '
                                          'current DOOM3 entry;native existing resolutions '
                                          'unchanged.'}],
  'excluded_lexeme_hypotheses': [{'lemma': 'Ferăstrău',
                                  'forms': [],
                                  'decision': 'Exact DOOM3 missing;older DOOM2 family excluded in '
                                              'full.'}],
  'dictionaries': [{'lemma': 'fierăstrău',
                    'url': 'https://dexonline.ro/definitie/fier%C4%83str%C4%83u/json',
                    'dex_definition_ids': ['870548'],
                    'doom3_definition_ids': ['1256512'],
                    'flexion_url': 'https://dexonline.ro/definitie/fier%C4%83str%C4%83u',
                    'flexion_authority': 'First DOOM3 Fierăstrău neuter '
                                         'table,fierăstrăul/fierăstraie',
                    'forms_note': 'Six complete current canonical normalized keys;leading ! is an '
                                  'editorial norm-change marker,not a lemma character. All six '
                                  'older Ferăstrău hypotheses excluded;only still-missing '
                                  'canonical keys proposed.',
                    'paraphrase': 'Unealtă sau mașină-unealtă cu lamă dințată pentru '
                                  'tăiere;familie de intrări a nodului existent,nu instrumentul '
                                  'muzical.; selected DEX sense/register and DOOM3 lexical '
                                  'gender/number checked, ordinary forms from First DOOM3 '
                                  'Fierăstrău neuter table,fierăstrăul/fierăstraie.'}],
  'sources': [{'url': 'https://dexonline.ro/definitie/fier%C4%83str%C4%83u/json',
               'paraphrase': 'Unealtă sau mașină-unealtă cu lamă dințată pentru tăiere;familie de '
                             'intrări a nodului existent,nu instrumentul muzical.; selected DEX '
                             'sense/register and DOOM3 lexical gender/number checked, ordinary '
                             'forms from First DOOM3 Fierăstrău neuter '
                             'table,fierăstrăul/fierăstraie.'},
              {'url': 'https://ro.wiktionary.org/wiki/fier%C4%83str%C4%83u',
               'paraphrase': 'Izvorul secundar încă trimite spre varianta Ferăstrău;această '
                             'preferință nu înlocuiește DOOM3 actual.'},
              {'url': 'https://dexonline.ro/definitie/fer%C4%83str%C4%83u/json',
               'paraphrase': 'Varianta Ferăstrău nu are intrare exactă DOOM3;paradigma disponibilă '
                             'este etichetată DOOM2 și nu este propusă.'},
              {'url': 'https://www.bosch-professional.com/ro/ro/panza-de-fierastrau-circular-expert-wood-cordless-pentru-fierastrau-de-banc-7561677-ocs-ac/',
               'paraphrase': 'Pagina producătorului confirmă sensul de sculă pentru tăierea '
                             'lemnului;cache direct tick4,reutilizat.'}],
  'link_targets': [],
  'source_acquisition_note': 'Canonical and auxiliary-variant JSON fetched directly with '
                             'pacing;variant evidence binds exclusion only. No bare '
                             'spelling-family ownership changed or resolved native input removed. '
                             'No new concept,description edit or edge authored for this existing '
                             'family.',
  'frequency': {'url': 'https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/ro/ro_50k.txt',
                'best_rank': 26553,
                'matched_form': 'fierăstrău',
                'role': 'Positive signal only; absence does not reject concrete everyday/school '
                        'vocabulary.'},
  'scope': 'Accepted after both once-only independent whole-batch web reviews and explicit verdict '
           'application;reviewed/unapplied/not_landed. No game round,target,recipe,route or '
           'runtime qualification.',
  'review_verdicts': {'factual': {'verdict': 'accept',
                                  'rationale': 'DOOM3 califică Fierăstrău și fierăstraie; ! este '
                                               'marker editorial, iar întreaga familie Ferăstrău '
                                               'rămâne exclusă.'},
                      'quality': {'verdict': 'accept',
                                  'rationale': 'The existing familiar saw owner receives only '
                                               'canonical fierăstraielor; current DOOM3 and '
                                               'complete exclusion of six older Ferăstrău '
                                               'hypotheses are verified.'}}},
 {'id': 'v119-cleste',
  'lemma': 'Clește',
  'kind': 'existing_input_family',
  'node_id': 'n_v32_workshop_hand_cleste',
  'games': ['Cald sau Rece', 'Lanțul Cuvintelor'],
  'sense': 'Unealta articulată pentru apucarea și manevrarea pieselor din nodul servit;excluse '
           'apendicele crustaceelor și pluralul neutru vechi.',
  'register': 'Selected everyday workshop/craft noun sense; unrelated,archaic/poetic-only meanings '
              'excluded;no instructions or clinical ruling.',
  'verified_forms': ['clește', 'cleștele', 'clești', 'cleștii', 'cleștelui', 'cleștilor'],
  'proposed_forms': ['cleștilor'],
  'already_resolved_forms': ['clește', 'cleștele', 'clești', 'cleștii', 'cleștelui'],
  'already_reserved_forms': [],
  'excluded_form_hypotheses': [],
  'dictionaries': [{'lemma': 'clește',
                    'url': 'https://dexonline.ro/definitie/cle%C8%99te/json',
                    'dex_definition_ids': ['847600'],
                    'doom3_definition_ids': ['1312237'],
                    'flexion_url': 'https://ro.wiktionary.org/wiki/cle%C8%99te',
                    'flexion_authority': 'DOOM3 masculine cleștele/clești lexical entry plus '
                                         'explicitly attributed Wiktionary masculine noun '
                                         'table;DEX page has no usable flexion table',
                    'forms_note': 'clește/cleștele/clești/cleștii/cleștelui/cleștilor;no old '
                                  'neuter plural,vocatives or crustacean meaning.',
                    'paraphrase': 'Unealta articulată pentru apucarea și manevrarea pieselor din '
                                  'nodul servit;excluse apendicele crustaceelor și pluralul neutru '
                                  'vechi.; selected DEX sense/register and DOOM3 lexical '
                                  'gender/number checked, ordinary forms from DOOM3 masculine '
                                  'cleștele/clești lexical entry plus explicitly attributed '
                                  'Wiktionary masculine noun table;DEX page has no usable flexion '
                                  'table.'}],
  'sources': [{'url': 'https://dexonline.ro/definitie/cle%C8%99te/json',
               'paraphrase': 'Unealta articulată pentru apucarea și manevrarea pieselor din nodul '
                             'servit;excluse apendicele crustaceelor și pluralul neutru vechi.; '
                             'selected DEX sense/register and DOOM3 lexical gender/number checked, '
                             'ordinary forms from DOOM3 masculine cleștele/clești lexical entry '
                             'plus explicitly attributed Wiktionary masculine noun table;DEX page '
                             'has no usable flexion table.'},
              {'url': 'https://ro.wiktionary.org/wiki/cle%C8%99te',
               'paraphrase': 'Tabelul masculin complet confirmă '
                             'cleștele/clești/cleștii/cleștelui/cleștilor și coincide cu '
                             'genul,numărul și articolul din DOOM3.'}],
  'link_targets': [],
  'source_acquisition_note': 'DOOM3 exact head/gender/article/plural checked in JSON;full ordinary '
                             'case table is explicitly attributed to Wiktionary,not claimed from '
                             'unavailable DEX flexion HTML.',
  'existing_sense_restriction': 'Same existing pliers owner n_v32_workshop_hand_cleste;grammatical '
                                'completion only,not a synonym.',
  'frequency': {'url': 'https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/ro/ro_50k.txt',
                'best_rank': 33841,
                'matched_form': 'clește',
                'role': 'Positive signal only; absence does not reject concrete everyday/school '
                        'vocabulary.'},
  'scope': 'Accepted after both once-only independent whole-batch web reviews and explicit verdict '
           'application;reviewed/unapplied/not_landed. No game round,target,recipe,route or '
           'runtime qualification.',
  'review_verdicts': {'factual': {'verdict': 'accept',
                                  'rationale': 'DOOM3 stabilește masculinul clește/clești; tabelul '
                                               'Wiktionary confirmă cleștilor pentru nodul '
                                               'existent, fără vechiul neutru.'},
                      'quality': {'verdict': 'accept',
                                  'rationale': 'The existing familiar pliers owner receives only '
                                               'cleștilor; DOOM3 masculine evidence plus the '
                                               'attributed Wiktionary table supports the full '
                                               'family.'}}},
 {'id': 'v119-surubelnita',
  'lemma': 'Șurubelniță',
  'kind': 'existing_input_family',
  'node_id': 'n_v32_workshop_hand_surubelnita',
  'games': ['Cald sau Rece', 'Lanțul Cuvintelor'],
  'sense': 'Unealta metalică pentru înșurubare și deșurubare din nodul servit.',
  'register': 'Selected everyday workshop/craft noun sense; unrelated,archaic/poetic-only meanings '
              'excluded;no instructions or clinical ruling.',
  'verified_forms': ['șurubelniță',
                     'șurubelnițe',
                     'șurubelnițele',
                     'șurubelniței',
                     'șurubelnițelor'],
  'proposed_forms': ['șurubelnițelor'],
  'already_resolved_forms': ['șurubelniță', 'șurubelnițe', 'șurubelnițele', 'șurubelniței'],
  'already_reserved_forms': [],
  'excluded_form_hypotheses': [],
  'dictionaries': [{'lemma': 'șurubelniță',
                    'url': 'https://dexonline.ro/definitie/%C8%99urubelni%C8%9B%C4%83/json',
                    'dex_definition_ids': ['838203'],
                    'doom3_definition_ids': ['1271964'],
                    'flexion_url': 'https://dexonline.ro/definitie/%C8%99urubelni%C8%9B%C4%83',
                    'flexion_authority': 'DOOM3 feminine șurubelniței/șurubelnițe plus first '
                                         'matching DOR noun table,not șurupelniță variant table',
                    'forms_note': 'șurubelniță/șurubelnița/șurubelnițe/șurubelnițele/șurubelniței/șurubelnițelor;no '
                                  'regional variants or vocatives.',
                    'paraphrase': 'Unealta metalică pentru înșurubare și deșurubare din nodul '
                                  'servit.; selected DEX sense/register and DOOM3 lexical '
                                  'gender/number checked, ordinary forms from DOOM3 feminine '
                                  'șurubelniței/șurubelnițe plus first matching DOR noun table,not '
                                  'șurupelniță variant table.'}],
  'sources': [{'url': 'https://dexonline.ro/definitie/%C8%99urubelni%C8%9B%C4%83/json',
               'paraphrase': 'Unealta metalică pentru înșurubare și deșurubare din nodul servit.; '
                             'selected DEX sense/register and DOOM3 lexical gender/number checked, '
                             'ordinary forms from DOOM3 feminine șurubelniței/șurubelnițe plus '
                             'first matching DOR noun table,not șurupelniță variant table.'},
              {'url': 'https://ro.wiktionary.org/wiki/%C8%99urubelni%C8%9B%C4%83',
               'paraphrase': 'Confirmă unealta pentru șuruburi și paradigma feminină cu genitivul '
                             'plural șurubelnițelor;lista regională nu este adoptată ca '
                             'sinonime.'}],
  'link_targets': [],
  'existing_sense_restriction': 'Same existing screwdriver owner '
                                'n_v32_workshop_hand_surubelnita;grammatical completion only,not a '
                                'synonym.',
  'frequency': {'url': 'https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/ro/ro_50k.txt',
                'best_rank': 25607,
                'matched_form': 'șurubelniță',
                'role': 'Positive signal only; absence does not reject concrete everyday/school '
                        'vocabulary.'},
  'scope': 'Accepted after both once-only independent whole-batch web reviews and explicit verdict '
           'application;reviewed/unapplied/not_landed. No game round,target,recipe,route or '
           'runtime qualification.',
  'review_verdicts': {'factual': {'verdict': 'accept',
                                  'rationale': 'Familia feminină a uneltei pentru șuruburi este '
                                               'confirmată; numai șurubelnițelor se adaugă la '
                                               'proprietarul existent.'},
                      'quality': {'verdict': 'accept',
                                  'rationale': 'The existing familiar screwdriver owner receives '
                                               'only șurubelnițelor; the full canonical family is '
                                               'verified without unscreened regional synonyms.'}}})

PROPOSAL_COUNTS = {'items': 49,
 'new_concepts': 44,
 'connections': 171,
 'missing_normalized_keys': 255,
 'new_concept_keys': 250,
 'existing_input_keys': 5,
 'existing_input_families': 5,
 'author_supported_exact_sense_synonym_families': 1,
 'verified_synonym_families': 1,
 'regional_input_keys': 0,
 'source_applied': False,
 'installed': 0,
 'player_visible_delta': '0/0/0',
 'accepted_reviewed_items': 49}

def build_nodes_and_edges():
    return {"nodes": NODES, "edges": EDGES, "aliases": ALIASES}
