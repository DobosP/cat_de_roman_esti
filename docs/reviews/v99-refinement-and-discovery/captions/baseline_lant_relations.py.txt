"""Short, orientation-independent captions for Lanț graph links.

Reviewed noun phrases bind the complete existing edge snapshot. They describe a
pair, so traversing a bidirectional edge backwards cannot turn an old verb into a
false assertion. Graph identity, orientation, labels, weights and routes are never
changed here. Unknown or altered edges get only a neutral relation-type caption;
missing links produce no caption. The finite mapping has no runtime mining/cache.
"""

from __future__ import annotations

from types import MappingProxyType

from .recipe_extensions import digest, record_snapshot

MAX_CAPTION_LENGTH = 34

# Exact unordered IDs -> (complete Edge snapshot SHA-256, reviewed noun phrase).
REVIEWED_CAPTIONS = MappingProxyType(
    {
        ("n_academia_romana", "n_mihai_eminescu"): (
            "e54634346e188580eb09153991915c2ca4a3d6391d892cffb94225e241c358e3",
            "academie și membru postum",
        ),
        ("n_academia_romana", "n_titu_maiorescu"): (
            "2b9f2a09e852d1fe6105bce2dd4912e2976443de1ae15cecec2c1cb0f7562c65",
            "academie și membru fondator",
        ),
        ("n_aeroportul_baneasa", "n_bucuresti"): (
            "ef06d3ae15a8b7328a0cbe438e311008fee350a41e8d9cb30347ee6f0f3b1ee6",
            "aeroport și oraș",
        ),
        ("n_aeroportul_baneasa", "n_v2sti_avion"): (
            "7d87f40c79edcaa22a9ea9fea94b77917b3a0d6ccb2990b025e337ad3ee39b55",
            "avion și aeroport",
        ),
        ("n_ansamblul_targu_jiu", "n_oltenia"): (
            "ab6269a5521bc7f3975faa8315b81319b69a44c2799984b7435e87f527739194",
            "ansamblu și regiune",
        ),
        ("n_ansamblul_targu_jiu", "n_poarta_sarutului"): (
            "0a101e588e5064bf2aac70f21415045d31b23608798df682b31c342a3f01141a",
            "sculptură și ansamblu",
        ),
        ("n_avram_iancu", "n_muntii_apuseni"): (
            "f3138d2e223d82b09fe5d4b80724db8cc804fc22015a8ceca1c26ba15c0df65f",
            "revoluționar și ținut natal",
        ),
        ("n_avram_iancu", "n_transilvania"): (
            "59bd45932bc282fb160aebc7d5e61bbc82f949312601f79cf50aa1485cce555b",
            "regiune și revoluționar",
        ),
        ("n_avram_iancu", "n_v11ist_revolutia_1848"): (
            "7bf17e8bbe50538f9292466cf9fb46a586fb9a528d7e0f5ef285b1759e5e5c26",
            "revoluționar și revoluție",
        ),
        ("n_bucegi", "n_v17geo_sfinxul_bucegi"): (
            "f3100ae18e641cbfa9d45b4984e7a66aefd27e222a4a022117084667ce7b3896",
            "formațiune stâncoasă și munți",
        ),
        ("n_bucegi", "n_v20geo_crucea_caraiman"): (
            "e2be04a03d927208fe6cc32004440adc1525deb307ba3c038c694c9b13048707",
            "monument și munții unde se află",
        ),
        ("n_bucovina", "n_putna"): (
            "3c70fb9e8afda8221d32fd59f0a5fd547047e508044b2a308b2cc894c066cf2a",
            "mănăstire și regiune",
        ),
        ("n_bucovina", "n_v11geo_suceava"): (
            "f4fbaf38aab680125649613977f564e06c4eab08e496d58e3b2a40243918da27",
            "oraș și regiune",
        ),
        ("n_bucovina", "n_voronet"): (
            "9b25b2f5387bfc47345a799562cd1065785c276048bd34faa6afcbad0fc4e9e3",
            "mănăstire și regiune",
        ),
        ("n_bucuresti", "n_muzeul_aviatiei_romane"): (
            "a84ed2a928eeb2232531525f2edf457b69b1f725108587cd24a8974a265e84d7",
            "muzeu și oraș",
        ),
        ("n_bucuresti", "n_v17geo_aeroportul_otopeni"): (
            "1557131ad8b8dcc284a5033647deaab6bf0b43a12289c57754c07fa82c37ac4b",
            "Capitală și aeroport",
        ),
        ("n_carpati", "n_olt"): (
            "215008878e9d2935a353308b66ca8ba67c9b9ec3229fa06496c0a4a5ab4135a4",
            "munți și râu",
        ),
        ("n_carpati", "n_v20geo_jiu"): (
            "1de78aa27b4f75082c6fcb2097d38c7feba79d1060528e005b6ae6138bc94cb6",
            "munți și râu",
        ),
        ("n_cluj_napoca", "n_transilvania"): (
            "e2d361aaf95d8998ed8880e8ccf14ec2d30f38afcff6e0217c6afa85644d0657",
            "oraș și regiune",
        ),
        ("n_cluj_napoca", "n_v17geo_salina_turda"): (
            "984f05c70ebf03ae54199cfdd5a8002a04fd381ad35f94ec0eb3947fc0d5c02c",
            "oraș și salină din apropiere",
        ),
        ("n_constantin_brancusi", "n_oltenia"): (
            "8a69213956242023db99398db696ed3319af000f7cac480b85e9b563b92e0234",
            "sculptor și regiune natală",
        ),
        ("n_constantin_brancusi", "n_poarta_sarutului"): (
            "a4685cd932408b9e67acaf80daa2c442a0e3c83894ab7ec8924e73d8bd4e0c13",
            "sculptură și sculptor",
        ),
        ("n_convorbiri_literare", "n_mihai_eminescu"): (
            "a41a9647a6a848ca8da98883df9f27dfb8a07f9313b90bf22c95a8ed87c1f742",
            "revistă și poet publicat",
        ),
        ("n_convorbiri_literare", "n_titu_maiorescu"): (
            "6666f7a7d8a40ef8821be52e519fde04540db663210135bba3b11aedd195d174",
            "revistă și îndrumător literar",
        ),
        ("n_convorbiri_literare", "n_v20lit_scrisoarea_iii"): (
            "87ceb1757b6635f2d00761c30d5ee19f46196d876af6edae8f8156dfb3ffc563",
            "poezie și revistă",
        ),
        ("n_convorbiri_literare", "n_v21lit_floare_albastra"): (
            "ac967d1bbf3203a48e74c42c56ed244a6367a2b3990b727c9da6c5d1737f0620",
            "poezie și revistă",
        ),
        ("n_delta_dunarii", "n_dunarea"): (
            "496682e9fbe61d9b7c4869cab460a1da56c59325667b88757c7a391fa7ed2e95",
            "fluviu și deltă",
        ),
        ("n_delta_dunarii", "n_marea_neagra"): (
            "1988fd21a88ec7b12b1c76e8e25a0f5dbd1abe3516097ad020fc8a3df992d855",
            "mare și deltă",
        ),
        ("n_dunarea", "n_olt"): (
            "831ff9108e7390f1dfe68b2bd4e74adf7e0184e0642ef702d395f364539d0bd6",
            "afluent și fluviu",
        ),
        ("n_dunarea", "n_v17geo_canal_dunare_marea_neagra"): (
            "8dd7e98504d90383244ac0a26ff184fc56814089586d31bdc5e34366d6ae26c6",
            "fluviu și canal navigabil",
        ),
        ("n_dunarea", "n_v20geo_jiu"): (
            "94efb96500569dface48fd452c02599076744bf27cab342aa057e7ceaa6c5276",
            "afluent și fluviu",
        ),
        ("n_dunarea", "n_v4geo_fluviu"): (
            "463eed72da2e73d2ee1425726133a33d6366f6696c9d0ec884fc0ae1c307f314",
            "fluviu și exemplu",
        ),
        ("n_ftv_pro_tv", "n_v11fil_romanii_au_talent"): (
            "9cc532347efd1d80ebc96e7fafadef279206ded1ed23d1343f72566816e455d9",
            "emisiune și post TV",
        ),
        ("n_ftv_pro_tv", "n_v11fil_vocea_romaniei"): (
            "fe5fbe7135dfcd54a82a63fef5b9c9ce36e1e99d653e337f91b1f29ef4d50539",
            "emisiune și post TV",
        ),
        ("n_gas_placinte_poale_brau", "n_v2gas_branza"): (
            "11fd5b31c8dc53a24e5a8510b104ac7e251913cd135a444762e1f3674b60a11d",
            "plăcintă și umplutură de brânză",
        ),
        ("n_gas_placinte_poale_brau", "n_v85_food_vanilie"): (
            "8da4ba575c82d9630c614542a52618c6de948e97bf685ccf869383ecbaec6b54",
            "plăcintă și aromă de vanilie",
        ),
        ("n_gas_sarmale", "n_v3gas_orez"): (
            "3a70a5d35de090740d12f9933c619883de83c1586af4613fdfa31defd7168e89",
            "sarmale și orezul din umplutură",
        ),
        ("n_gas_sarmale", "n_v4gas_carne"): (
            "92c06349274d1d5fca98ef97ba832c2d5511aa17b845606421e86e8fd4a1d5b5",
            "sarmale și carnea din umplutură",
        ),
        ("n_gheorghe_hagi", "n_spt_romania_argentina_1994"): (
            "df06ff23f880f8fc7d98ec5a8e37e907c874243a6050eafdc269f379b8de4967",
            "fotbalist și meci",
        ),
        ("n_gheorghe_hagi", "n_v17spo_anghel_iordanescu"): (
            "feb47bac504e4b01f23c22dbc0e04478415a548a6a0ff95da77c5a2652b5dd5d",
            "fotbalist și antrenor",
        ),
        ("n_iasi", "n_junimea"): (
            "d0b2d518f9ef860294f4a8f7d3881c3dfae06532d9261a3fd831e3f39cf5dd08",
            "oraș și societate literară",
        ),
        ("n_iasi", "n_mihai_eminescu"): (
            "e8ba0ee3a1b2051e539b8de2e769d5f741a02f6a470dfce37c40548c2d5fbdc5",
            "scriitor și oraș",
        ),
        ("n_iasi", "n_moldova"): (
            "320a3800ce9523021504add45b4f1cd98600086f34782a86da2ee88c3cee1304",
            "capitală istorică și regiune",
        ),
        ("n_ion_creanga", "n_junimea"): (
            "437b4677da2b098c93c2b2d0a2100987534882c00366ca22f0d6705aafe7165c",
            "scriitor și societate literară",
        ),
        ("n_ion_creanga", "n_mihai_eminescu"): (
            "fe1f298ce9f36e79d9bc2995f69f80b7c4093dce88f6e252cfa0f8d3dc2bced4",
            "prieteni scriitori",
        ),
        ("n_ion_creanga", "n_moldova"): (
            "1f362d7e5bc2af5ab13b7bccd5ab4256e4b241865098e9a1a0ab98a6b680fe1f",
            "scriitor și regiune natală",
        ),
        ("n_ion_creanga", "n_v23lit_capra_cu_trei_iezi"): (
            "f78f6fa9095f82f92ccb2cba5d3d84a283f191e67789edb7fea4c86ec3867c7c",
            "autor și poveste",
        ),
        ("n_ion_creanga", "n_v23lit_povestea_porcului"): (
            "30fac2788b9e08aec2f46e87b51b1adaa3080f1fd45e1984dd612755cd72d111",
            "autor și poveste",
        ),
        ("n_ion_creanga", "n_v23lit_punguta_cu_doi_bani"): (
            "bfad921708b2f3cf8a0ab8a944f45130d77fe57b56717c88b9ab6a251acc6fad",
            "autor și poveste",
        ),
        ("n_istx_adunarea_blaj", "n_transilvania"): (
            "95d9a8133133b4fc322600d48d008df5adb697d58b60183bfea1087e6d6e5d11",
            "adunare istorică și regiune",
        ),
        ("n_istx_adunarea_blaj", "n_v11ist_revolutia_1848"): (
            "7790b8ca186c3b12b2746f2031bedc301d64faac035c871f499bb23060518acd",
            "adunare și revoluție",
        ),
        ("n_junimea", "n_mihai_eminescu"): (
            "913b5e8bf1d7280702fa0408f5e7474f10ee7322e9ebe19dd5d057b7674ced5e",
            "societate literară și poet",
        ),
        ("n_junimea", "n_titu_maiorescu"): (
            "6412370d2d1ef93aa2fee71a382b63fcb21603728ce544c580a5ee627b355e52",
            "societate literară și mentor",
        ),
        ("n_marea_neagra", "n_v17geo_canal_dunare_marea_neagra"): (
            "eb68d4cf4ca31d31403e9a794af557ded9ecffed24da817289a38eed4238bba7",
            "mare și canal navigabil",
        ),
        ("n_marea_neagra", "n_v4geo_fluviu"): (
            "b4e53f54f16f07235ee3df567a9bd696cb597fe815a428f664e8860eb54bee70",
            "fluviu și mare",
        ),
        ("n_mihai_eminescu", "n_v20lit_scrisoarea_iii"): (
            "b5dd449c9cfdf295a41d3cdc90a3733136e0ce051a88ea5b904d31ef8991a075",
            "autor și poezie",
        ),
        ("n_mihai_eminescu", "n_v21lit_floare_albastra"): (
            "32457950ad274c26a73f0311ff1c597a1bdde8aaf84e1eaf31580814a7c97b7f",
            "autor și poezie",
        ),
        ("n_muntii_apuseni", "n_v11ist_rascoala_1784"): (
            "3e4c9e53fbdd9037f952b6636872f2335c5f58d29994e7e4ec871f492f892d2e",
            "răscoală și ținutul ei",
        ),
        ("n_muntii_apuseni", "n_v20geo_cheile_turzii"): (
            "80da1ab4293c1d48f3636d309b5250a1c02ccfc2d56ef0923a2adf8cb40f4271",
            "chei și munții din care fac parte",
        ),
        ("n_muzeul_aviatiei_romane", "n_v2sti_avion"): (
            "557fd5a504590d50fc1e88d75c0346198258017fcd78ac6c7feb8bd043fef558",
            "avion și muzeu de aviație",
        ),
        ("n_muzeul_brukenthal", "n_sibiu"): (
            "5b34ed4e76d417027be7da5bf864aba574c091998059f490c60e0f083a2d3684",
            "muzeu și oraș",
        ),
        ("n_muzeul_brukenthal", "n_v2art_muzeu"): (
            "698e21f6d61883f52e62ab9a716c16c802819fcf0964d687c51bf923a51312d6",
            "muzeu și categorie",
        ),
        ("n_oltenia", "n_targu_jiu"): (
            "7af0c0494296fd4e982225747438bcad7971d5ed493a7c67768fc56b4327ffa1",
            "oraș și regiune",
        ),
        ("n_poarta_sarutului", "n_targu_jiu"): (
            "423546eab58ec56acb5565e941fb5769b813d9f215ea28c25b98b1b25f25bb1c",
            "sculptură și oraș",
        ),
        ("n_putna", "n_stefan_cel_mare"): (
            "8ed11d47193dbdf9588124b493561ec23592ddc294fbe02d80b6c71d48ee867a",
            "domnitor și ctitorie",
        ),
        ("n_romantism", "n_v20lit_scrisoarea_iii"): (
            "b42299c924228c4adde90c20dbb839bf13bc875b416cc48238497953e04f7c10",
            "poezie și curent literar",
        ),
        ("n_romantism", "n_v21lit_floare_albastra"): (
            "fccfe32eba79f60f827391c4ef4ea220c89b9307edfbdc84e10fd78bf66639b3",
            "poezie și curent literar",
        ),
        ("n_sibiu", "n_v20art_muzeul_astra"): (
            "7e04758ebb4714eb68a9856c791ba97055b17a0cb414feb773c740221d230f8c",
            "muzeu și oraș",
        ),
        ("n_spt_cupa_campionilor_1986", "n_spt_helmut_duckadam"): (
            "ab4624d472dc5f098c4197d0cf4391f1d26028c490cbf51d702df33979bb6c89",
            "portar și competiție",
        ),
        ("n_spt_cupa_campionilor_1986", "n_v21spo_emeric_ienei"): (
            "bf8b2f7fb850a339f310b599191e45f38b2c5c6692ac2ab298516f019ec11474",
            "antrenor și competiție",
        ),
        ("n_spt_david_popovici", "n_spt_lotul_olimpic_romania"): (
            "ed0278d0761c161e6e8109a089a3f6fe9707890a24c65b8618a0155bd3e35ae5",
            "sportiv și lot olimpic",
        ),
        ("n_spt_david_popovici", "n_v17spo_aur_paris_2024"): (
            "0a260f158293f446ecbd5e953808b700dad9c769ace62bd07efee7a8bb18498e",
            "sportiv și medalie de aur",
        ),
        ("n_spt_finala_sevilla_1986", "n_spt_helmut_duckadam"): (
            "4108b70b2adddf6ac388676bb177237df448f5a97e172f5d7a4fe909bf8e97ce",
            "portar și finală",
        ),
        ("n_spt_finala_sevilla_1986", "n_v21spo_emeric_ienei"): (
            "ce098cca509e79302b7333306886ad944fee32a517d24f5ced9d98b33e0c0d09",
            "antrenor și finală",
        ),
        ("n_spt_helmut_duckadam", "n_spt_steaua_1986"): (
            "226084c019a58e782e38f76ded0f5bab70e728e49ae5a217fa16d26905e06fb6",
            "echipă și portar",
        ),
        ("n_spt_lotul_olimpic_romania", "n_v19spo_jo_paris_2024"): (
            "9ee7d386c8cb47e32b6b046e5f0cf83776964a762b37de16e9875e35bc4370ae",
            "lot olimpic și competiție",
        ),
        ("n_spt_romania_argentina_1994", "n_spt_tricolorii"): (
            "a87a52382658fc07f207819107bbc49b3b7b937b0e33aff84eeb9291c48bc898",
            "meci și echipă națională",
        ),
        ("n_spt_romania_argentina_1994", "n_spt_world_cup_1994"): (
            "db1b098296d52dec2077187d5a516cc311efd83898299d505b91b64b53e6ddcf",
            "meci și turneu",
        ),
        ("n_spt_steaua_1986", "n_v21spo_emeric_ienei"): (
            "29f9b3a8d1de8beb0d5fe2cb042c81c30e4e93a8f753b6c7e17deb504fe577d9",
            "echipă și antrenor",
        ),
        ("n_spt_tricolorii", "n_v17spo_anghel_iordanescu"): (
            "bf310901c146985cd9d9f5141d3656e667e9e5e7a709da0321f517814d050315",
            "echipă și selecționer",
        ),
        ("n_spt_world_cup_1994", "n_v17spo_anghel_iordanescu"): (
            "65921f443bf188998b6bebfc7542e6cd839daf2fe5775bc3acd2ff5a55e30f66",
            "selecționer și turneu",
        ),
        ("n_stefan_cel_mare", "n_v11geo_suceava"): (
            "6f5663336e1fb96110d282c610647e8a3e85aaa75a4a8af6743b40c2bbd9a6ee",
            "domnitor și capitală medievală",
        ),
        ("n_stefan_cel_mare", "n_voronet"): (
            "178de0f5529dd7c500d6ef0c689f974cc45331a894819d808fc926fdbccddb86",
            "domnitor și ctitorie",
        ),
        ("n_transilvania", "n_v11ist_rascoala_1784"): (
            "f11a72a4077cfcb62df9bd573d91b1286a087f68f8ebb4aa865b8c2e44432095",
            "răscoală și regiune",
        ),
        ("n_v11fil_romanii_au_talent", "n_v20fil_pavel_bartos"): (
            "f9dafada6a6a0459bca4251ac7c568cd2bbb8e5eff13a39a041d9dacffa3da0d",
            "emisiune și prezentator",
        ),
        ("n_v11fil_romanii_au_talent", "n_v2fil_concurs_tv"): (
            "641e43cbde9f2d0452ae743ffa327ba81b808b99fcc5476e315c15e4d53c285d",
            "emisiune și tip de concurs",
        ),
        ("n_v11fil_vocea_romaniei", "n_v20fil_pavel_bartos"): (
            "c7c0ea24982772f36f2a2ed983c5b8637878ef3bd6d43f4b6daf6867dde6c870",
            "emisiune și prezentator",
        ),
        ("n_v11fil_vocea_romaniei", "n_v2fil_concurs_tv"): (
            "56969030a78ea7443f83f16afcaf06af77dbc431703ade9e90a5e2ab3acad2d7",
            "emisiune și tip de concurs",
        ),
        ("n_v11gas_ciorba_perisoare", "n_v3gas_orez"): (
            "62b43bf0cc25bbeaa8251f0efb8bf12b69561f91a8633a942a46238af935cdd9",
            "ciorbă și ingredient opțional",
        ),
        ("n_v11gas_ciorba_perisoare", "n_v4gas_carne"): (
            "d0e13a6d83b04571140a94095a4b77629a2f39db8ac6d44b104d56a887d8b805",
            "ciorbă și carnea din perișoare",
        ),
        ("n_v17gas_pasca", "n_v2gas_branza"): (
            "5d0ab3103ffafb9bb8ceb437b589e0b1fe506a8e9bc6fb9bd67ad8110a8d5924",
            "pască și umplutură de brânză",
        ),
        ("n_v17gas_pasca", "n_v85_food_vanilie"): (
            "efe3858dc0d5b792326c78c0f321c461f16d8d8c23666b8b3c8c55352b1321a1",
            "pască și aromă de vanilie",
        ),
        ("n_v17geo_aeroportul_otopeni", "n_v2sti_avion"): (
            "9ee9fb16bcc893a3add9b315840a646a4b2edce2a5dc707514873251fd9960ea",
            "avion și aeroport",
        ),
        ("n_v17geo_babele", "n_v17geo_sfinxul_bucegi"): (
            "946ae401898ecb935d2975092abd6260e94f69e70ff3a06761fad657cdda964c",
            "formațiuni stâncoase vecine",
        ),
        ("n_v17geo_babele", "n_v20geo_crucea_caraiman"): (
            "dee299c9923f3f87e058b631b8550976fa5ff06e0e73972e36e3bb67605c0b05",
            "stânci și monument din Bucegi",
        ),
        ("n_v17geo_salina_turda", "n_v20geo_cheile_turzii"): (
            "6b9a91bcebd720248e823455f9957c2f458b4d70a7669c99b98777d33b22fb6f",
            "obiective din zona Turda",
        ),
        ("n_v17spo_aur_paris_2024", "n_v19spo_jo_paris_2024"): (
            "338cb6bda558bd89491d7eaf15b35b899004afdfe48f4140e3eb70711796baa7",
            "medalie și ediție olimpică",
        ),
        ("n_v20art_muzeul_astra", "n_v2art_muzeu"): (
            "d8864d3a7006e1f688d3a1a4e4b5dfe3a15810a732e00d063197a4852b2fbd04",
            "muzeu și categorie",
        ),
        ("n_v23lit_capra_cu_trei_iezi", "n_v3lit_carte"): (
            "b67ee4e0011a076bbb7688b51da04a182157e8c5abc6e326f74807db27df16a8",
            "poveste și carte",
        ),
        ("n_v23lit_povestea_porcului", "n_v3lit_carte"): (
            "efd98729fbc5a6609232c22d815dc5687728d9ac233cd6e18e7b8c545fbff1c2",
            "poveste și carte",
        ),
        ("n_v23lit_punguta_cu_doi_bani", "n_v3lit_carte"): (
            "fc9dd1203ad04c51e33b6050f9a81478847d86718f6f8085b373db54b3843606",
            "poveste și carte",
        ),
        ("n_v24_food_pantry_zahar", "n_v86_food_crema_vanilie"): (
            "b0f1282f303f01a4fa15a81f0a7d0c295ee2130e14bd2dca3e6a85daa02f025f",
            "cremă și îndulcitor",
        ),
        ("n_v24_food_pantry_zahar", "n_v86_food_zahar_pudra"): (
            "7248dee307657c4be52b3da207b9cc4521385fe0a683556c347ae162cb38ac35",
            "zahăr și formă măcinată",
        ),
        ("n_v24_food_snack_biscuit", "n_v84_food_cuptor"): (
            "ef26c0c388e1c0e973311e802a72a8a68c9fe96a8b5dcc0d569fe2649155fbc5",
            "cuptor și biscuiți copți",
        ),
        ("n_v24_food_snack_biscuit", "n_v90_food_firimitura"): (
            "2cea5133d564d78610f4948ead10fdede52d5a0d0a48a7ed467ac1a9838b2674",
            "biscuit și bucățele desprinse",
        ),
        ("n_v4gas_paine", "n_v84_food_cuptor"): (
            "7fbb959dea82f68c3951c0c17aeefb4eebf00746d2ea42d505ecf972744cc67d",
            "cuptor și pâine coaptă",
        ),
        ("n_v4gas_paine", "n_v90_food_firimitura"): (
            "45eb8429ce1f32dce4e5bf402e61f652efac3451519052171a16978b5f460c5e",
            "pâine și bucățele desprinse",
        ),
        ("n_v86_food_crema_vanilie", "n_v87_food_cremsnit"): (
            "e016e4794c3c48ebf8cfb3581452c2508cb74b05b30f1682236bfac5d6e00cb9",
            "prăjitură și umplutură",
        ),
        ("n_v86_food_frisca", "n_v86_food_zahar_pudra"): (
            "48feda733ce0739d13b0458caaad82b2ec801f10e52bc32cdfe3573602807d2c",
            "frișcă și îndulcitor opțional",
        ),
        ("n_v86_food_frisca", "n_v87_food_tort_diplomat"): (
            "04a7be12c1fb9a689ab2266e5404855c0bb1537cbfd91ab215d1c18a9e0d11aa",
            "tort și frișca din cremă",
        ),
        ("n_v86_food_zahar_pudra", "n_v87_food_cremsnit"): (
            "0f6375bcdec5eddb1dec28d902552826a37f9969f2eb64bb3ccfe7094fd20e95",
            "prăjitură și pudră dulce",
        ),
        ("n_v86_food_zahar_pudra", "n_v87_food_piscot"): (
            "6037c540b23886196b80006de4b424d85b3065dd91e82f1f1a0aa07ffed34b74",
            "pișcot și zahăr de presărat",
        ),
        ("n_v87_food_piscot", "n_v87_food_tort_diplomat"): (
            "9dc08ffe90fc0d66318750013f6b86fbc20ffa160ddfba6ae7d5e7aeb14388bd",
            "tort și margine cu pișcoturi",
        ),
    }
)

_FALLBACKS = MappingProxyType(
    {
        "created_by": "creator și operă",
        "part_of": "parte și întreg",
        "is_a": "exemplu și categorie",
        "contemporary_of": "contemporani",
    }
)


def caption(service, a: str, b: str) -> str:
    """Describe an actual allowed edge without asserting a traversal direction."""
    edge = service.link(a, b)
    if edge is None:
        return ""
    reviewed = REVIEWED_CAPTIONS.get(tuple(sorted((a, b))))
    if reviewed is not None and digest(record_snapshot(edge)) == reviewed[0]:
        return reviewed[1]
    return _FALLBACKS.get(edge.relation, "legătură directă")
