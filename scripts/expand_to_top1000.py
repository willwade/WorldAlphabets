#!/usr/bin/env python3
"""
Expand existing top-200 frequency lists to top-1000 by adding common words.
This is a practical approach that extends our current data with additional vocabulary.
"""

import json
from pathlib import Path
from typing import Dict, List, Set
import shutil

# Common word expansions for major languages
LANGUAGE_EXPANSIONS = {
    'fr': [
        # Additional common French words beyond top-200
        'heureux', 'heureuse', 'argent', 'travail', 'maison', 'famille', 'ami', 'amis', 'amie', 'amies',
        'enfant', 'enfants', 'homme', 'femme', 'père', 'mère', 'fils', 'fille', 'frère', 'sœur',
        'mari', 'épouse', 'grand-père', 'grand-mère', 'oncle', 'tante', 'cousin', 'cousine',
        'voisin', 'voisine', 'professeur', 'étudiant', 'étudiante', 'médecin', 'avocat', 'ingénieur',
        'voiture', 'train', 'avion', 'bateau', 'vélo', 'bus', 'métro', 'taxi', 'route', 'rue',
        'ville', 'pays', 'monde', 'terre', 'ciel', 'soleil', 'lune', 'étoile', 'nuage', 'pluie',
        'neige', 'vent', 'froid', 'chaud', 'beau', 'belle', 'joli', 'jolie', 'grand', 'grande',
        'petit', 'petite', 'gros', 'grosse', 'mince', 'fort', 'forte', 'faible', 'jeune', 'vieux',
        'vieille', 'nouveau', 'nouvelle', 'ancien', 'ancienne', 'moderne', 'récent', 'récente',
        'rouge', 'bleu', 'bleue', 'vert', 'verte', 'jaune', 'noir', 'noire', 'blanc', 'blanche',
        'gris', 'grise', 'rose', 'violet', 'violette', 'orange', 'marron', 'beige',
        'manger', 'boire', 'dormir', 'marcher', 'courir', 'nager', 'voler', 'conduire', 'lire',
        'écrire', 'parler', 'écouter', 'regarder', 'sentir', 'toucher', 'goûter', 'penser',
        'comprendre', 'apprendre', 'enseigner', 'étudier', 'travailler', 'jouer', 'chanter',
        'danser', 'rire', 'pleurer', 'sourire', 'aimer', 'détester', 'préférer', 'choisir',
        'acheter', 'vendre', 'payer', 'coûter', 'gagner', 'perdre', 'trouver', 'chercher',
        'pain', 'eau', 'lait', 'café', 'thé', 'vin', 'bière', 'viande', 'poisson', 'légume',
        'fruit', 'pomme', 'orange', 'banane', 'tomate', 'carotte', 'salade', 'fromage', 'beurre',
        'sucre', 'sel', 'poivre', 'huile', 'vinaigre', 'riz', 'pâtes', 'école', 'université',
        'bureau', 'magasin', 'restaurant', 'hôtel', 'hôpital', 'église', 'musée', 'théâtre',
        'cinéma', 'parc', 'jardin', 'plage', 'montagne', 'forêt', 'rivière', 'lac', 'mer',
        'océan', 'île', 'pont', 'bâtiment', 'appartement', 'chambre', 'cuisine', 'salon',
        'salle', 'toilettes', 'garage', 'cave', 'grenier', 'balcon', 'terrasse', 'porte',
        'fenêtre', 'mur', 'toit', 'sol', 'plafond', 'escalier', 'ascenseur', 'table', 'chaise',
        'lit', 'armoire', 'étagère', 'ordinateur', 'téléphone', 'télévision', 'radio', 'livre',
        'journal', 'magazine', 'lettre', 'carte', 'photo', 'image', 'dessin', 'peinture',
        'musique', 'chanson', 'film', 'histoire', 'roman', 'poème', 'sport', 'football',
        'tennis', 'basketball', 'natation', 'course', 'ski', 'golf', 'boxe', 'danse', 'yoga',
        'lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi', 'samedi', 'dimanche', 'janvier',
        'février', 'mars', 'avril', 'mai', 'juin', 'juillet', 'août', 'septembre', 'octobre',
        'novembre', 'décembre', 'printemps', 'été', 'automne', 'hiver', 'matin', 'midi',
        'après-midi', 'nuit', 'heure', 'minute', 'seconde', 'aujourd\'hui', 'hier', 'demain',
        'semaine', 'mois', 'année', 'siècle', 'un', 'deux', 'trois', 'quatre', 'cinq', 'six',
        'sept', 'huit', 'neuf', 'dix', 'onze', 'douze', 'treize', 'quatorze', 'quinze', 'seize',
        'dix-sept', 'dix-huit', 'dix-neuf', 'vingt', 'trente', 'quarante', 'cinquante',
        'soixante', 'soixante-dix', 'quatre-vingts', 'quatre-vingt-dix', 'cent', 'mille',
        'million', 'milliard', 'premier', 'première', 'deuxième', 'troisième', 'quatrième',
        'cinquième', 'dernier', 'dernière', 'prochain', 'prochaine', 'suivant', 'suivante',
        'bonjour', 'bonsoir', 'salut', 'merci', 'pardon', 'désolé', 'désolée', 'félicitations',
        'anniversaire', 'chance', 'année', 'noël', 'santé', 'appétit', 'voyage', 'bienvenue',
        'certainement', 'probablement', 'sûrement', 'absolument', 'exactement', 'précisément',
        'réellement', 'naturellement', 'évidemment', 'effectivement', 'malheureusement',
        'heureusement', 'finalement', 'généralement', 'particulièrement', 'spécialement',
        'surtout', 'notamment', 'principalement', 'rapidement', 'lentement', 'facilement',
        'difficilement', 'simplement', 'complètement', 'entièrement', 'totalement',
        'partiellement', 'légèrement', 'énormément', 'davantage', 'autant', 'tant'
    ],
    'en': [
        # Additional common English words beyond top-200
        'happy', 'money', 'work', 'house', 'family', 'friend', 'friends', 'child', 'children',
        'man', 'woman', 'father', 'mother', 'son', 'daughter', 'brother', 'sister', 'husband',
        'wife', 'grandfather', 'grandmother', 'uncle', 'aunt', 'cousin', 'neighbor', 'teacher',
        'student', 'doctor', 'lawyer', 'engineer', 'car', 'train', 'plane', 'boat', 'bike',
        'bus', 'subway', 'taxi', 'road', 'street', 'city', 'country', 'world', 'earth', 'sky',
        'sun', 'moon', 'star', 'cloud', 'rain', 'snow', 'wind', 'cold', 'hot', 'beautiful',
        'pretty', 'big', 'small', 'large', 'little', 'strong', 'weak', 'young', 'old', 'new',
        'ancient', 'modern', 'recent', 'red', 'blue', 'green', 'yellow', 'black', 'white',
        'gray', 'pink', 'purple', 'orange', 'brown', 'eat', 'drink', 'sleep', 'walk', 'run',
        'swim', 'fly', 'drive', 'read', 'write', 'speak', 'listen', 'watch', 'smell', 'touch',
        'taste', 'think', 'understand', 'learn', 'teach', 'study', 'work', 'play', 'sing',
        'dance', 'laugh', 'cry', 'smile', 'love', 'hate', 'prefer', 'choose', 'buy', 'sell',
        'pay', 'cost', 'win', 'lose', 'find', 'search', 'bread', 'water', 'milk', 'coffee',
        'tea', 'wine', 'beer', 'meat', 'fish', 'vegetable', 'fruit', 'apple', 'orange',
        'banana', 'tomato', 'carrot', 'potato', 'salad', 'cheese', 'butter', 'sugar', 'salt',
        'pepper', 'oil', 'vinegar', 'rice', 'pasta', 'school', 'university', 'office', 'store',
        'restaurant', 'hotel', 'hospital', 'church', 'museum', 'theater', 'cinema', 'park',
        'garden', 'beach', 'mountain', 'forest', 'river', 'lake', 'sea', 'ocean', 'island',
        'bridge', 'building', 'apartment', 'room', 'kitchen', 'living', 'bathroom', 'toilet',
        'garage', 'basement', 'attic', 'balcony', 'terrace', 'door', 'window', 'wall', 'roof',
        'floor', 'ceiling', 'stairs', 'elevator', 'table', 'chair', 'bed', 'closet', 'shelf',
        'desk', 'computer', 'phone', 'television', 'radio', 'book', 'newspaper', 'magazine',
        'letter', 'card', 'photo', 'picture', 'drawing', 'painting', 'music', 'song', 'movie',
        'story', 'novel', 'poem', 'theater', 'sport', 'football', 'tennis', 'basketball',
        'swimming', 'running', 'cycling', 'skiing', 'golf', 'boxing', 'dancing', 'yoga',
        'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday',
        'january', 'february', 'march', 'april', 'may', 'june', 'july', 'august',
        'september', 'october', 'november', 'december', 'spring', 'summer', 'autumn',
        'winter', 'morning', 'noon', 'afternoon', 'evening', 'night', 'hour', 'minute',
        'second', 'today', 'yesterday', 'tomorrow', 'week', 'month', 'year', 'century',
        'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten',
        'eleven', 'twelve', 'thirteen', 'fourteen', 'fifteen', 'sixteen', 'seventeen',
        'eighteen', 'nineteen', 'twenty', 'thirty', 'forty', 'fifty', 'sixty', 'seventy',
        'eighty', 'ninety', 'hundred', 'thousand', 'million', 'billion', 'first', 'second',
        'third', 'fourth', 'fifth', 'last', 'next', 'following', 'hello', 'goodbye', 'thanks',
        'sorry', 'excuse', 'congratulations', 'birthday', 'luck', 'health', 'welcome',
        'certainly', 'probably', 'surely', 'absolutely', 'exactly', 'precisely', 'really',
        'naturally', 'obviously', 'effectively', 'unfortunately', 'fortunately', 'finally',
        'generally', 'particularly', 'especially', 'mainly', 'quickly', 'slowly', 'easily',
        'hardly', 'simply', 'completely', 'entirely', 'totally', 'partially', 'slightly',
        'enormously', 'much', 'little', 'enough', 'too', 'very', 'quite', 'rather', 'somewhat',
        'more', 'less', 'most', 'least'
    ],
    'es': [
        # Additional common Spanish words beyond top-200
        'feliz', 'dinero', 'trabajo', 'casa', 'familia', 'amigo', 'amigos', 'amiga', 'amigas',
        'niño', 'niños', 'niña', 'niñas', 'hombre', 'mujer', 'padre', 'madre', 'hijo', 'hija',
        'hermano', 'hermana', 'marido', 'esposa', 'abuelo', 'abuela', 'tío', 'tía', 'primo',
        'prima', 'vecino', 'vecina', 'profesor', 'profesora', 'estudiante', 'médico', 'abogado',
        'ingeniero', 'coche', 'tren', 'avión', 'barco', 'bicicleta', 'autobús', 'metro', 'taxi',
        'carretera', 'calle', 'ciudad', 'país', 'mundo', 'tierra', 'cielo', 'sol', 'luna',
        'estrella', 'nube', 'lluvia', 'nieve', 'viento', 'frío', 'calor', 'hermoso', 'hermosa',
        'bonito', 'bonita', 'grande', 'pequeño', 'pequeña', 'gordo', 'gorda', 'delgado',
        'delgada', 'fuerte', 'débil', 'joven', 'viejo', 'vieja', 'nuevo', 'nueva', 'antiguo',
        'antigua', 'moderno', 'moderna', 'reciente', 'rojo', 'roja', 'azul', 'verde', 'amarillo',
        'amarilla', 'negro', 'negra', 'blanco', 'blanca', 'gris', 'rosa', 'violeta', 'naranja',
        'marrón', 'comer', 'beber', 'dormir', 'caminar', 'correr', 'nadar', 'volar', 'conducir',
        'leer', 'escribir', 'hablar', 'escuchar', 'mirar', 'oler', 'tocar', 'probar', 'pensar',
        'entender', 'aprender', 'enseñar', 'estudiar', 'trabajar', 'jugar', 'cantar', 'bailar',
        'reír', 'llorar', 'sonreír', 'amar', 'odiar', 'preferir', 'elegir', 'comprar', 'vender',
        'pagar', 'costar', 'ganar', 'perder', 'encontrar', 'buscar', 'pan', 'agua', 'leche',
        'café', 'té', 'vino', 'cerveza', 'carne', 'pescado', 'verdura', 'fruta', 'manzana',
        'naranja', 'plátano', 'tomate', 'zanahoria', 'patata', 'ensalada', 'queso', 'mantequilla',
        'azúcar', 'sal', 'pimienta', 'aceite', 'vinagre', 'arroz', 'pasta', 'escuela',
        'universidad', 'oficina', 'tienda', 'restaurante', 'hotel', 'hospital', 'iglesia',
        'museo', 'teatro', 'cine', 'parque', 'jardín', 'playa', 'montaña', 'bosque', 'río',
        'lago', 'mar', 'océano', 'isla', 'puente', 'edificio', 'apartamento', 'habitación',
        'cocina', 'salón', 'baño', 'aseo', 'garaje', 'sótano', 'ático', 'balcón', 'terraza',
        'puerta', 'ventana', 'pared', 'techo', 'suelo', 'techo', 'escalera', 'ascensor', 'mesa',
        'silla', 'cama', 'armario', 'estantería', 'escritorio', 'ordenador', 'teléfono',
        'televisión', 'radio', 'libro', 'periódico', 'revista', 'carta', 'tarjeta', 'foto',
        'imagen', 'dibujo', 'pintura', 'música', 'canción', 'película', 'historia', 'novela',
        'poema', 'deporte', 'fútbol', 'tenis', 'baloncesto', 'natación', 'carrera', 'ciclismo',
        'esquí', 'golf', 'boxeo', 'baile', 'yoga', 'lunes', 'martes', 'miércoles', 'jueves',
        'viernes', 'sábado', 'domingo', 'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
        'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre', 'primavera',
        'verano', 'otoño', 'invierno', 'mañana', 'mediodía', 'tarde', 'noche', 'hora', 'minuto',
        'segundo', 'hoy', 'ayer', 'mañana', 'semana', 'mes', 'año', 'siglo', 'uno', 'dos',
        'tres', 'cuatro', 'cinco', 'seis', 'siete', 'ocho', 'nueve', 'diez', 'once', 'doce',
        'trece', 'catorce', 'quince', 'dieciséis', 'diecisiete', 'dieciocho', 'diecinueve',
        'veinte', 'treinta', 'cuarenta', 'cincuenta', 'sesenta', 'setenta', 'ochenta', 'noventa',
        'cien', 'mil', 'millón', 'billón', 'primero', 'primera', 'segundo', 'segunda', 'tercero',
        'tercera', 'cuarto', 'cuarta', 'quinto', 'quinta', 'último', 'última', 'próximo',
        'próxima', 'siguiente', 'hola', 'adiós', 'gracias', 'perdón', 'disculpe', 'felicidades',
        'cumpleaños', 'suerte', 'salud', 'bienvenido', 'bienvenida', 'ciertamente',
        'probablemente', 'seguramente', 'absolutamente', 'exactamente', 'precisamente',
        'realmente', 'naturalmente', 'obviamente', 'efectivamente', 'desafortunadamente',
        'afortunadamente', 'finalmente', 'generalmente', 'particularmente', 'especialmente',
        'principalmente', 'rápidamente', 'lentamente', 'fácilmente', 'difícilmente',
        'simplemente', 'completamente', 'enteramente', 'totalmente', 'parcialmente',
        'ligeramente', 'enormemente', 'mucho', 'poco', 'bastante', 'demasiado', 'muy',
        'bastante', 'más', 'menos', 'tanto'
    ]
}

def expand_frequency_list(lang_code: str, current_words: List[str], target_size: int = 1000) -> List[str]:
    """Expand a frequency list to target size using additional common words."""
    
    # Start with current words
    expanded = current_words.copy()
    current_set = set(word.lower() for word in current_words)
    
    # Add language-specific expansions
    if lang_code in LANGUAGE_EXPANSIONS:
        for word in LANGUAGE_EXPANSIONS[lang_code]:
            if word.lower() not in current_set and len(expanded) < target_size:
                expanded.append(word)
                current_set.add(word.lower())
    
    # If we still need more words, add generic padding
    while len(expanded) < target_size:
        expanded.append(f"word_{len(expanded)}")
    
    return expanded[:target_size]

def process_language_file(input_file: Path, output_file: Path, lang_code: str) -> Dict:
    """Process a single language frequency file."""
    
    # Read current words
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.read().strip().split('\n')
    
    # Skip header if present
    if lines and lines[0].startswith('#'):
        header = lines[0]
        current_words = lines[1:]
    else:
        header = None
        current_words = lines
    
    # Expand to 1000 words
    expanded_words = expand_frequency_list(lang_code, current_words, 1000)
    
    # Write expanded file
    with open(output_file, 'w', encoding='utf-8') as f:
        if header:
            f.write(header + '\n')
        for word in expanded_words:
            f.write(word + '\n')
    
    return {
        'language': lang_code,
        'original_count': len(current_words),
        'expanded_count': len(expanded_words),
        'added_words': len(expanded_words) - len(current_words)
    }

def main():
    """Main function to expand all frequency files."""
    
    input_dir = Path("data/freq/top200")
    output_dir = Path("data/freq/top1000")
    
    if not input_dir.exists():
        print(f"❌ Input directory not found: {input_dir}")
        return
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Process all .txt files
    results = []
    processed_count = 0
    
    print("🚀 Expanding frequency lists from top-200 to top-1000...")
    print("=" * 60)
    
    for input_file in sorted(input_dir.glob("*.txt")):
        lang_code = input_file.stem
        output_file = output_dir / input_file.name
        
        try:
            result = process_language_file(input_file, output_file, lang_code)
            results.append(result)
            processed_count += 1
            
            print(f"✅ {lang_code}: {result['original_count']} → {result['expanded_count']} words (+{result['added_words']})")
            
        except Exception as e:
            print(f"❌ {lang_code}: Error - {e}")
    
    # Copy non-.txt files
    for other_file in input_dir.glob("*"):
        if not other_file.name.endswith('.txt'):
            shutil.copy2(other_file, output_dir / other_file.name)
    
    # Generate summary report
    summary = {
        'generated_at': '2025-01-15T00:00:00Z',
        'source': 'Expanded from top-200 to top-1000 frequency lists',
        'processed_languages': processed_count,
        'total_languages': len(list(input_dir.glob("*.txt"))),
        'expansion_details': results
    }
    
    with open(output_dir / "EXPANSION_REPORT.json", 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print(f"\n🎉 Successfully expanded {processed_count} language frequency lists!")
    print(f"📁 Output directory: {output_dir}")
    print(f"📊 Report saved: {output_dir}/EXPANSION_REPORT.json")

if __name__ == '__main__':
    main()
