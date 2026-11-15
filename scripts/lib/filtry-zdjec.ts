/**
 * Filtry zdjęć do atlasu i filmów: wspólne dla Wikimedia Commons (scripts/atlas-pobierz.ts) i Openverse (scripts/atlas-openverse.ts).
 * Liczą się budowle, mury, rzeźby i wykopaliska; odpadają ludzie pozujący do aparatu, wycieczki, reklamy, logo i przyroda.
 */
// podkategorie i pliki ze zbliżeniami konstrukcji: detale, mury, bloki, reliefy, napisy, wnętrza…
export const DETAL = /\b(details?|close[- ]?ups?|stonework|masonry|walls?|blocks?|stones?|megaliths?|reliefs?|carvings?|carved|inscriptions?|hieroglyphs?|petroglyphs?|glyphs?|interiors?|joints?|columns?|capitals?|doors?|doorways?|gates?|niches?|windows?|statues?|sculptures?|murals?|frescos?|frescoes|ceilings?|chambers?|corridors?|tunnels?|stairs|steps|altars?|stelae?|monoliths?|engravings?|ornaments?|construction|architecture)\b/i;
// pomijane: mapy, plany, logo, znaczki, filmy i zdjęcia ludzi przy okazji
export const ZBEDNE = /\b(maps?|plans?|diagrams?|logos?|coats? of arms|stamps?|postcards?|banknotes?|coins?|videos?|audio|people|tourists?|selfies?|signs?|tickets?|events?|concerts?|festivals?|souvenirs?|hotels?|restaurants?|buses|trains?|vehicles?|airports?)\b/i;
// zdjęcia ludzi pozujących do aparatu, wycieczek, reklam biur podróży i z logo – nie pokazujemy (liczą się budowle i rzeźby)
export const LUDZIE_KAT = /\b(people|persons?|tourists?|tourism|selfies?|portraits?|groups? of|men|women|girls?|boys?|children|kids|famil(y|ies)|couples?|weddings?|logos?|watermarks?|advertis\w*|tour (operators?|guides?)|travel agenc\w*|camel rid\w*|horse rid\w*)\b/i;
export const LUDZIE_TXT = /\b(tours?|tour group|egypta|travel|trip|visit(ing|ors?)?|me at|with (my|friends)|friends|family|posing|selfie|group photo|portrait|wedding|honeymoon|holidays?|vacation|we at|us at|tourists?|people|crowd|guide|camel ride|military|army|soldiers?|paratroopers?|freefall|parade|police|members|band|concert|ceremony|celebration|events?|festival|riders?|jinete|camell?os|horses?|camels?|show|exercise|conference|minister|president|delegation|team|students?|trier|to sort|ministe\w*|reist|besuch\w*|visite|embajad\w*|ambassador)\b/i;
// rzeźby, reliefy, napisy, mury i kamienne konstrukcje – najcenniejsze zdjęcia
export const RZEZBA = /\b(sculptur\w*|statues?|reliefs?|carv\w*|rzeźb\w*|figur\w*|stel(a|ae|e)|idols?|lions?|sphinx\w*|petroglyph\w*|hieroglyph\w*|inscriptions?|solar (sign|symbol)|znak solarny)\b/i;
export const KONSTRUKCJA = /\b(walls?|masonry|blocks?|stonework|megalith\w*|ramparts?|wał\w*|ruins?|excavations?|tunnels?|chambers?|crypts?|columns?|gates?|doorways?|temples?|tombs?|pyramids?)\b/i;
// przyroda zamiast budowli (grzyby w lesie pod Ślężą, ptaki nad piramidą…)
export const PRZYRODA = /\b(fung[ui]\w*|mushrooms?|grzyb\w*|macrolepiota|agaric\w*|boletus|plants?|flowers?|flora|fauna|insects?|butterfl\w*|moths?|beetles?|spiders?|birds?|aves|animals?|mammals?|reptiles?|snakes?|lizards?|lichens?|moss(es)?|bryophyt\w*|trees? in|forest floor|leaves|orchids?|wildlife|dogs?|cats?|cows?|sheep|goats?|deer)\b/i;

/** true, gdy zdjęcia nie należy pokazywać (tekst: nazwa pliku, opis, kategorie lub tagi) */
export const odrzucZdjecie = (tekst: string, kategorie = "") => {
  const rzezba = RZEZBA.test(tekst); // „Girl with fish” to rzeźba, a nie zdjęcie ludzi
  if (!rzezba && (LUDZIE_KAT.test(kategorie) || LUDZIE_TXT.test(tekst))) return true;
  if (/\b(huts?|hostels?|schronisk\w*|przystan\w*|bus stops?|parking|signposts?|tablice?)\b/i.test(tekst)) return true;
  return PRZYRODA.test(`${tekst} ${kategorie}`) || ZBEDNE.test(tekst.slice(0, 160));
};
