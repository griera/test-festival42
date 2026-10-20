#!/usr/bin/env python3
import random
import argparse

def generate_large_csv(output_filename, num_books, num_talks, num_signings):
    """
    Generates a synthetic festival CSV file containing books, talks, and signings
    based on custom user-defined quantities.
    """
    # Base header matching your exact format
    header = "type;title;ean;author;publisher;collection;category;quantity;price;discount;tax;total;location;datetime\n"
    
    # Base rows provided by the user
    base_rows = [
        "book;ACCELERANDO;9788498891621;CHARLES STROSS;ALAMUT;FONDO;FICCION MODERNA Y CONTEMPORANEA, CIENCIA FICCION, Ciencia ficci¢n;10;28,80;0;4;299,52;;",
        "book;MOIRAS;9786316541369;VILAR MADRUGA,ELAINE;FERA EDICIONES;MUJERES QUE LEEN MUJERES;CUENTOS DE TERROR Y FANTASMAS, CUENTOS;20;22,02;0;4;458,02;;",
        "book;DANTESCAS;9786316541079;AMPUERO,MARIA FERNANDA;FERA EDICIONES;MUJERES QUE LEEN MUJERES;ANTOLOGIAS (NO POETICAS), FICCION MODERNA Y CONTEMPORANEA, CUENTOS DE TERROR Y FANTASMAS, CUENTOS CLASICOS DE TERROR Y FANTASMAS;20;22,02;0;4;458,02;;",
        "book;VERTIGO EN LA BOCA;9791399034868;SARMIENTO,CAROLINA;BAJAMAR EDITORES;AMARILLA;POESIA, POESIA DE POETAS INDIVIDUALES;2;11,54;0;4;24,00;;",
        "book;GOTICO DIVINO;9791399023626;ARRABAL,MARINA/FAE,ANNA/G MORA,ALBA/GOM;HORROR VACUI;HORROR VACUI;CUENTOS DE TERROR Y FANTASMAS, FICCION RELIGIOSA Y ESPIRITUAL, MENTE, CUERPO Y ESPIRITU, Terror contempor neo e historias de fantasmas, Ficci¢n de lo oculto (ocultismo);3;18,17;0;4;56,69;;",
        "book;LA ROSA DE LAS NIEBLAS;9788412931426;ROBLES,LOLA;CRONONAUTA;CIENCIA FICCION;FICCION MODERNA Y CONTEMPORANEA, CIENCIA FICCION, CIENCIA FICCION CLASICA, Ficci¢n moderna y contempor nea: general y literar, Ciencia ficci¢n, Ciencia ficci¢n cl sica;8;19,23;0;4;159,99;;",
        "book;REGRESO A GAOZU;9788412571776;GONZALEZ, ISA J,;CRONONAUTA;CIENCIA FICCION;FICCION MODERNA Y CONTEMPORANEA, CIENCIA FICCION, Ficci¢n moderna y contempor nea: general y literar, Ciencia ficci¢n: exploraci¢n espacial;3;20,67;0;4;64,49;;",
        "book;ULTIMA LUZ DE TRALIA,LA;9788412059953;GONZALEZ,ISA J;CRONONAUTA;CIENCIA FICCION;FICCION MODERNA Y CONTEMPORANEA, CIENCIA FICCION, ESTUDIOS HOMOSEXUALES, FEMINISMO Y TEORIA FEMINISTA, Ficci¢n moderna y contempor nea: general y literar, Ciencia ficci¢n, Estudios / temas sobre la comunidad LGBTQ+;3;14,42;0;4;44,99;;",
        "book;CONSECUENCIAS NATURALES;9788494795862;BARCELO,ELIA;CRONONAUTA;CIENCIA FICCION;FICCION MODERNA Y CONTEMPORANEA, CIENCIA FICCION, FEMINISMO Y TEORIA FEMINISTA, Ficci¢n moderna y contempor nea: general y literar, Ciencia ficci¢n, Feminismo y teor¡a feminista;2;15,38;0;4;31,99;;",
        "book;LO QUE CUENTAN LOS MONSTRUOS;9788419293435;SOLSONA ASENSIO,GEMMA;APACHE;ANTOLOGIAS LUJO;CUENTOS DE TERROR Y FANTASMAS, CUENTOS CLASICOS DE TERROR Y FANTASMAS, FANTASIA, MITOS Y LEYENDAS NARRADOS COMO FICCION;6;20,67;0;4;128,98;;",
        "book;HISTORIA DE LO FANTASTICO EN LAS NARRATIVAS LATINOAMERICANA;9788491923060;AA,VV;IBEROAMERICANA VERVUERT;AMERICANA EYSTETTENSIA;LITERATURA: HISTORIA Y CRITICA, HISTORIA, LATINOAMERICA, M,xico, Centroam,rica, Sudam,rica, Latinoam,rica, Literatura: historia y cr¡tica;3;34,62;0;4;108,01;;",
        "book;EL ANACRONOPETE;9788494890833;ENRIQUE GASPAR Y RIMBAU/FRANCISCO GOMEZ;EDITORIAL INLIBRIS;RECUERDOS DEL FUTURO;CIENCIA FICCION, CIENCIA FICCION CLASICA, ESPAÑA;3;19,23;0;4;60,00;;",
        "book;CUENTOS ILUSTRADOS COMPLETOS;9788494890826;FABRA Y DEAS, NILO MARIA;GASPAR & RIMBAU;RECUERDOS DEL FUTURO;FANTASIA, EUROPA DEL SUR;3;15,38;0;4;47,99;;",
        "book;CUENTOS EN EL ESPACIO Y EL TIEMPO;9788412119367;GARCIA GUTIERREZ,ALBERTO;GASPAR & RIMBAU;RECUERDOS DEL FUTURO;CIENCIA FICCION, FANTASIA;8;15,38;0;4;127,96;;",
        "book;BRUJAS EN EL ARTE, LAS;9789464991086;PARE, ALIX;ILUS BOOKS S L;GENERAL;HISTORIA DEL ARTE / ESTILOS DE ARTE Y DISEÑO, FORMAS DE EXPRESION ARTISTICA, BRUJERIA, BRUJERIA Y WICCA, Artes: formas de expresi¢n art¡stica;20;12,45;0;4;258,96;;",
        "book;DIABLO EN EL ARTE, EL;9789464991055;PARE, ALIX;ILUS BOOKS S L;GENERAL;HISTORIA DEL ARTE / ESTILOS DE ARTE Y DISEÑO, FORMAS DE EXPRESION ARTISTICA, MENTE, CUERPO Y ESPIRITU, LIBROS DE REGALO, Artes: formas de expresi¢n art¡stica;20;12,45;0;4;258,96;;",
        "book;HORROTURISMO CO(S)MICO;9791399057638;SANCHEZ MACANAS,IBAN M;LITERUP;FANTASIA;FANTASIA, HUMOR;8;16,34;0;4;135,95;;",
        "talk;TAULA RODONA: EL TERROR CONTEMPORANI;;MARÍA FERNANDA AMPUERO, ELAINE VILAR MADRUGA;;;;0;0;0;0;0;Escenari 1 (Fabra i Coats);06/11/2026 17:00",
        "signing;SESSIÓ DE SIGNATURES CRONONAUTA;;ISA J. GONZÁLEZ, LOLA ROBLES;;;;0;0;0;0;0;Mòdul de Signatures A;07/11/2026 18:30"
    ]

    # Vocabulary pools for synthetic generation
    adjectives = [
        "CRONICAS", "SOMBRAS", "ECOS", "LABERINTO", "IMPERIO", "VIAJE", "SECRETO", "REINO", "AKASHICA", "FUTURO",
        "VALLE", "MUTACION", "ESTRELLA", "BIBLIOTECA", "ORBITA", "NOCTURNO", "INFINITO", "ESPEJO", "CICLO", "ARKHAM",
        "VALKIRIA", "FANTASMA", "PARADOJA", "NEXUS", "SINGULARIDAD", "HECATOMBE", "LABORATORIO", "MUTANTE", "STELLAR",
        "ABISMO", "HERMANDAD", "PROFECIA", "ATOMIC", "FRACTAL", "QUIMERA", "ALQUIMIA", "SANTUARIO", "VANGUARDIA"
    ]

    nouns = [
        "DEL TIEMPO", "DE MARTE", "DEL ABISMO", "SYNTH", "QUANTUM", "DE LA NIEBLA", "DE CRISTAL", "OFERTA", "CYBER", "STEAMPUNK",
        "DE LA LUNA", "SINTETICO", "DE ACERO", "MULTIVERSO", "DE LA OBSIDIANA", "NEON", "DE LA TIERRA ROTA", "NEBULOSA",
        "PARADOJA", "DEL VACIO", "DE LOS ANCESTROS", "DE LA TORRE", "DEL CICLÓN", "DE LA SOMBRA", "DE LA MATRIX",
        "DE LOS TITANES", "DEL OCASO", "DE LA GALAXIA", "DEL CORTEX", "DE LA ALQUIMIA", "DEL ECLIPSE", "DE LA ETERNIDAD"
    ]

    authors = [
        "MARTÍNEZ, CARLOS", "GARCÍA, LAURA", "RODRÍGUEZ, PERE", "SMITH, JOHN", "KIM, MIN-HO", "DU PONT, CLAIRE", "VANCE, JACK", "MENDOZA, ELENA",
        "ASIMOV, ISAAC", "LE GUIN, URSULA", "SHELLEY, MARY", "VANDERMEER, JEFF", "CHAMBERS, BECKY", "GARCÍA BINDER, MARTA",
        "GÓMEZ, NURIA", "SOLER, MARC", "PLAZA, JOAN", "CASTILLO, SOFÍA", "NAVARRO, HÉCTOR", "ESTÉVEZ, BEATRIZ",
        "SANDOVAL, RAÚL", "GIBSON, WILLIAM", "PK DICK, PHILIP", "CLARKE, ARTHUR C.", "LOVECRAFT, H.P.", "SHELLEY, MARY",
        "SHELBY, THOMAS", "WALTERS, ANNA", "HERNÁNDEZ, CARLES", "BLANCO, MIREIA", "ROIG, CLAUDIA", "FERNÁNDEZ, BORJA"
    ]

    publishers = [
        "ALAMUT", "CRONONAUTA", "EDICIONES MINOTAURO", "NOCTURNA", "LITERUP", "VERSIÓN BETA",
        "MINOTAURO", "INSÓLITA EDITORIAL", "PULP BOOKS", "EDITORIAL LUNAR", "FANTASY EDICIONES", "NEO LIBROS",
        "FIBRA EDITORIAL", "GAIA EDICIONES", "VALHALLA PRESS", "HORROR VACUI", "BAJAMAR EDITORES", "APACHE"
    ]

    collections = [
        "FANTASIA OSCURA", "CIENCIA FICCION MODERNA", "NEOPULP", "FUTUROS IMPERFECTOS", "GENERAL",
        "FANTASÍA ÉPICA", "ESPECULATIVA", "HORROR CÓSMICO", "CIENCIA FICCIÓN CLÁSICA", "NARRATIVA EXTRAÑA", "TERROR URBANO",
        "RECUERDOS DEL FUTURO", "MUJERES QUE LEEN MUJERES", "AMARILLA", "ANTOLOGIAS LUJO", "FONDO"
    ]

    categories = [
        "CIENCIA FICCION, FANTASIA", "CUENTOS DE TERROR Y FANTASMAS", "FICCION MODERNA Y CONTEMPORANEA", "POESIA",
        "ANTOLOGIAS (NO POETICAS), FANTASIA", "FICCION RELIGIOSA Y ESPIRITUAL, MENTE, CUERPO Y ESPIRITU",
        "HISTORIA DEL ARTE / ESTILOS DE ARTE Y DISEÑO, BRUJERIA Y WICCA", "CIENCIA FICCION CLASICA, ESPAÑA",
        "FANTASIA, HUMOR", "ESTUDIOS HOMOSEXUALES, FEMINISMO Y TEORIA FEMINISTA", "LITERATURA: HISTORIA Y CRITICA, LATINOAMERICA"
    ]

    locations_talks = ["Escenari 1 (Fabra i Coats)", "Auditori Central", "Sala Polivalent B"]
    locations_signings = ["Mòdul de Signatures A", "Mòdul de Signatures B", "Punt de Trobada Librers"]
    days = ["04/11/2026", "05/11/2026", "06/11/2026", "07/11/2026", "08/11/2026"]
    hours = ["11:00", "12:30", "16:00", "17:30", "19:00"]

    generated_rows = []

    # Generate Books dynamically based on parameter
    for i in range(1, num_books + 1):
        title = f"{random.choice(adjectives)} {random.choice(nouns)} {i}"
        ean = f"97884{random.randint(100000000, 999999999)}"
        author = random.choice(authors)
        pub = random.choice(publishers)
        col = random.choice(collections)
        cat = random.choice(categories)
        qty = random.randint(2, 25)
        price_val = round(random.uniform(10.0, 35.0), 2)
        price_str = str(price_val).replace('.', ',')
        total_val = round(price_val * qty, 2)
        total_str = str(total_val).replace('.', ',')
        
        row = f"book;{title};{ean};{author};{pub};{col};{cat};{qty};{price_str};0;4;{total_str};;"
        generated_rows.append(row)

    # Generate Talks dynamically based on parameter
    for i in range(1, num_talks + 1):
        title = f"CONFERÈNCIA MAGNA: ELS MONS DE FICCIÓ #{i}"
        speaker = f"{random.choice(authors)} & {random.choice(authors)}"
        loc = random.choice(locations_talks)
        dt = f"{random.choice(days)} {random.choice(hours)}"
        
        row = f"talk;{title};;{speaker};;;;0;0;0;0;0;{loc};{dt}"
        generated_rows.append(row)

    # Generate Signings dynamically based on parameter
    for i in range(1, num_signings + 1):
        title = f"SESSIÓ DE SIGNATURES ESPECIAL #{i}"
        author = random.choice(authors)
        loc = random.choice(locations_signings)
        dt = f"{random.choice(days)} {random.choice(hours)}"
        
        row = f"signing;{title};;{author};;;;0;0;0;0;0;{loc};{dt}"
        generated_rows.append(row)

    # Write all data to the output file
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(header)
        for r in base_rows:
            f.write(r + "\n")
        for r in generated_rows:
            f.write(r + "\n")

    print(f"Successfully generated {output_filename} with {len(base_rows) + len(generated_rows)} total rows!")

if __name__ == "__main__":
    # Set up argument parser with detailed usage and execution examples
    parser = argparse.ArgumentParser(
        description="Generate a synthetic CSV file containing festival data (books, talks, and signings) for performance and scalability testing.",
        epilog="Examples of execution:\n"
               "  1. Default run (500 books, 20 talks, 30 signings):\n"
               "     python3 generate_large_csv.py\n\n"
               "  2. Custom quantities:\n"
               "     python3 generate_large_csv.py --books 100 --talks 5 --signings 10\n\n"
               "  3. Custom quantities and output file name:\n"
               "     python3 generate_large_csv.py -b 50 -t 2 -s 3 -o test_dataset.csv\n\n"
               "  4. Display help menu:\n"
               "     python3 generate_large_csv.py --help",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "-b", "--books",
        type=int,
        default=500,
        help="Number of synthetic books to generate (default: 500)"
    )
    parser.add_argument(
        "-t", "--talks",
        type=int,
        default=20,
        help="Number of synthetic talks/conferences to generate (default: 20)"
    )
    parser.add_argument(
        "-s", "--signings",
        type=int,
        default=30,
        help="Number of synthetic book-signing sessions to generate (default: 30)"
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default="data_synthetic.csv",
        help="Output filename for the generated CSV (default: data_synthetic.csv)"
    )

    args = parser.parse_args()

    # Execute main generator function with parsed parameters
    generate_large_csv(args.output, args.books, args.talks, args.signings)
