"""AI specialty suggestion engine using TF-IDF and cosine similarity."""

# Specialty keyword corpus for TF-IDF matching
SPECIALTY_DESCRIPTIONS = {
    "Cardiologie": "douleur thoracique palpitations essoufflement coeur arythmie hypertension infarctus tachycardie chest pain heart palpitations shortness breath",
    "Dermatologie": "peau boutons rougeurs acné eczéma psoriasis démangeaisons éruption cutanée taches skin rash acne eczema itching spots",
    "Pédiatrie": "enfant bébé fièvre nourrisson vaccin croissance pédiatrique développement child baby fever vaccine growth pediatric",
    "Gynécologie": "femme grossesse menstruation règles contraception ovaire utérus maternité pregnancy menstruation contraception ovary uterus",
    "Ophtalmologie": "yeux vision vue flou lunettes cataracte glaucome rétine eyes vision blurry glasses cataracts glaucoma retina",
    "Dentisterie": "dents douleur dentaire caries gencives mâchoire extraction plombage teeth dental pain cavities gums jaw extraction",
    "ORL": "oreille nez gorge sinusite angine otite rhinite allergie voix enrouement ear nose throat sinusitis tonsillitis otitis allergy",
    "Neurologie": "tête migraine mémoire vertige épilepsie tremblement paralysie nerf headache migraine memory dizziness epilepsy tremor nerve",
    "Radiologie": "radio scanner IRM imagerie os fracture diagnostic xray scan MRI imaging bone fracture",
    "Médecine Générale": "fièvre fatigue rhume grippe douleur général consultation médecin fever fatigue cold flu pain general checkup",
}


def suggest_specialty(patient_text: str, top_n: int = 3) -> list:
    """
    Suggest medical specialties based on patient-described symptoms.

    Uses TF-IDF vectorization and cosine similarity to match the patient's
    text against specialty keyword corpora.

    Args:
        patient_text: Free-text description of symptoms.
        top_n: Number of top specialty suggestions to return.

    Returns:
        List of dicts with 'specialty' and 'confidence' (percentage) keys.
    """
    if not patient_text or not patient_text.strip():
        return [{'specialty': 'Médecine Générale', 'confidence': 100.0}]

    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity

    specialties = list(SPECIALTY_DESCRIPTIONS.keys())
    descriptions = list(SPECIALTY_DESCRIPTIONS.values())

    corpus = descriptions + [patient_text]
    vectorizer = TfidfVectorizer(analyzer='word', ngram_range=(1, 2))
    tfidf_matrix = vectorizer.fit_transform(corpus)

    patient_vector = tfidf_matrix[-1]
    specialty_vectors = tfidf_matrix[:-1]

    similarities = cosine_similarity(patient_vector, specialty_vectors).flatten()
    top_indices = similarities.argsort()[::-1][:top_n]

    results = []
    for idx in top_indices:
        if similarities[idx] > 0:
            results.append({
                'specialty': specialties[idx],
                'confidence': round(float(similarities[idx]) * 100, 1),
            })

    return results if results else [{'specialty': 'Médecine Générale', 'confidence': 100.0}]
