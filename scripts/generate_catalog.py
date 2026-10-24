#!/usr/bin/env python3
import random
import argparse

def generate_random_schedule(days, hours):
    """
    Generates schedule strings: 70% empty.
    If generated: 50% single date, 25% two dates, 25% three dates.
    """
    # 70% chance of empty schedule
    if random.random() < 0.7:
        return ""

    # Determine number of dates (50% -> 1, 25% -> 2, 25% -> 3)
    rand_val = random.random()
    if rand_val < 0.50:
        num_dates = 1
    elif rand_val < 0.75:
        num_dates = 2
    else:
        num_dates = 3

    # Select unique day/hour combinations
    selected_schedules = set()
    while len(selected_schedules) < num_dates:
        dt = f"{random.choice(days)} {random.choice(hours)}"
        selected_schedules.add(dt)

    return ", ".join(selected_schedules)

def generate_large_csv(output_filename, num_books, num_talks, num_signings):
    """
    Generates a synthetic raw festival catalog CSV file containing books, talks, 
    and signings with 'type' as the first column and 'location' & 'datetime' at the end.
    """
    header = "type;ean;title;author;publisher;distributor;category;price;theme;schedule;location;datetime\n"

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
        "DE LOS TITANES", "DEL OCASO", "DE LA GALAXIA", "DEL CORTEX", "DEL ECLIPSE", "DE LA ETERNIDAD"
    ]

    authors = [
        "MARTÍNEZ, CARLOS", "GARCÍA, LAURA", "RODRÍGUEZ, PERE", "SMITH, JOHN", "KIM, MIN-HO", "DU PONT, CLAIRE", "VANCE, JACK", "MENDOZA, ELENA",
        "ASIMOV, ISAAC", "LE GUIN, URSULA", "SHELLEY, MARY", "VANDERMEER, JEFF", "CHAMBERS, BECKY", "GARCÍA BINDER, MARTA",
        "GÓMEZ, NURIA", "SOLER, MARC", "PLAZA, JOAN", "CASTILLO, SOFÍA", "NAVARRO, HÉCTOR", "ESTÉVEZ, BEATRIZ",
        "SANDOVAL, RAÚL", "GIBSON, WILLIAM", "PK DICK, PHILIP", "CLARKE, ARTHUR C.", "LOVECRAFT, H.P.",
        "SHELBY, THOMAS", "WALTERS, ANNA", "HERNÁNDEZ, CARLES", "BLANCO, MIREIA", "ROIG, CLAUDIA", "FERNÁNDEZ, BORJA"
    ]

    publishers = [
        "ALAMUT", "CRONONAUTA", "EDICIONES MINOTAURO", "NOCTURNA", "LITERUP", "VERSIÓN BETA",
        "MINOTAURO", "INSÓLITA EDITORIAL", "PULP BOOKS", "EDITORIAL LUNAR", "FANTASY EDICIONES", "NEO LIBROS",
        "FIBRA EDITORIAL", "GAIA EDICIONES", "VALHALLA PRESS", "HORROR VACUI", "BAJAMAR EDITORES", "APACHE"
    ]

    distributors = [
        "DISTRIBUCIONS BCN", "ÀGORA DISTRIBUCIÓ", "LOGISBOOK", "DISTRIBUIDORA CATALANA", "UDL DISTRIBUCIÓ", "PULP DISTRO"
    ]

    categories = ["FICCIO", "FANTASIA", "CIENCIA FICCIO", "TERROR", "POESIA", "GENERAL"]

    themes = [
        "CUENTOS DE TERROR Y FANTASMAS, FICCION MODERNA",
        "CIENCIA FICCION CLASICA, ESPAÑA",
        "FANTASIA, HUMOR",
        "ESTUDIOS HOMOSEXUALES, FEMINISMO Y TEORIA FEMINISTA",
        ""
    ]

    locations_talks = ["Escenari 1 (Fabra i Coats)", "Auditori Central", "Sala Polivalent B"]
    locations_signings = ["Mòdul de Signatures A", "Mòdul de Signatures B", "Punt de Trobada Llibreters"]
    days = ["04/11/2026", "05/11/2026", "06/11/2026", "07/11/2026", "08/11/2026"]
    hours = ["10:00", "10:30", "11:00", "11:30", "12:00", "12:30", "15:00", "15:30", "16:00", "16:30", "17:00", "17:30", "18:00", "18:30"]

    generated_rows = []

    # Generate Books
    for i in range(1, num_books + 1):
        ean = f"97884{random.randint(100000000, 999999999)}"
        title = f"{random.choice(adjectives)} {random.choice(nouns)}"
        author = random.choice(authors)
        publisher = random.choice(publishers)
        distributor = random.choice(distributors)
        category = random.choice(categories)
        
        # 10% chance of empty price to test 0.0 fallback
        price_str = "" if random.random() < 0.1 else str(round(random.uniform(10.0, 35.0), 2)).replace('.', ',')

        theme = random.choice(themes)
        schedule = generate_random_schedule(days, hours)
        location = ""
        datetime_val = ""

        row = f"book;{ean};{title};{author};{publisher};{distributor};{category};{price_str};{theme};{schedule};{location};{datetime_val}"
        generated_rows.append(row)

    # Generate Talks
    for i in range(1, num_talks + 1):
        ean = ""
        title = f"TAULA RODONA: EL TERROR CONTEMPORANI #{i}"
        author = f"{random.choice(authors)}, {random.choice(authors)}"
        publisher = ""
        distributor = ""
        category = ""
        price_str = "0"
        theme = ""
        schedule = ""
        location = random.choice(locations_talks)
        datetime_val = f"{random.choice(days)} {random.choice(hours)}"

        row = f"talk;{ean};{title};{author};{publisher};{distributor};{category};{price_str};{theme};{schedule};{location};{datetime_val}"
        generated_rows.append(row)

    # Generate Signings
    for i in range(1, num_signings + 1):
        ean = ""
        title = f"SESSIÓ DE SIGNATURES CRONONAUTA #{i}"
        author = random.choice(authors)
        publisher = ""
        distributor = ""
        category = ""
        price_str = "0"
        theme = ""
        schedule = ""
        location = random.choice(locations_signings)
        datetime_val = f"{random.choice(days)} {random.choice(hours)}"

        row = f"signing;{ean};{title};{author};{publisher};{distributor};{category};{price_str};{theme};{schedule};{location};{datetime_val}"
        generated_rows.append(row)

    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(header)
        for r in generated_rows:
            f.write(r + "\n")

    total = len(generated_rows)
    print(f"Successfully generated {output_filename} with {total} records ({num_books} books, {num_talks} talks, {num_signings} signings)!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate synthetic raw festival catalog CSV file.",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("-b", "--books", type=int, default=500, help="Number of books (default: 500)")
    parser.add_argument("-t", "--talks", type=int, default=20, help="Number of talks (default: 20)")
    parser.add_argument("-s", "--signings", type=int, default=30, help="Number of signings (default: 30)")
    parser.add_argument("-o", "--output", type=str, default="data/catalog_raw.csv", help="Output CSV path (default: data/catalog_raw.csv)")

    args = parser.parse_args()
    generate_large_csv(args.output, args.books, args.talks, args.signings)
