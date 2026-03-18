from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

# Simple keyword-based drug interaction database
INTERACTIONS = {
    ("aspirin","warfarin"):         ("HIGH","Increased bleeding risk. Avoid combination."),
    ("aspirin","ibuprofen"):        ("MOD","Reduced aspirin efficacy. Use paracetamol instead."),
    ("metronidazole","alcohol"):    ("HIGH","Severe nausea/vomiting reaction. Avoid alcohol."),
    ("iron","calcium"):             ("MOD","Calcium reduces iron absorption. Give 2 hours apart."),
    ("folic acid","phenytoin"):     ("MOD","Phenytoin reduces folate absorption."),
    ("magnesium sulfate","nifedipine"): ("HIGH","Risk of hypotension and neuromuscular blockade."),
    ("methyldopa","iron"):          ("MOD","Iron reduces methyldopa absorption."),
    ("doxycycline","antacids"):     ("MOD","Antacids reduce doxycycline absorption by up to 80%."),
    ("amoxicillin","warfarin"):     ("MOD","Increased anticoagulant effect possible."),
    ("metformin","alcohol"):        ("MOD","Increased risk of lactic acidosis."),
    ("tramadol","ssri"):            ("HIGH","Risk of serotonin syndrome."),
    ("nsaids","antihypertensive"):  ("MOD","NSAIDs may reduce antihypertensive effects."),
    ("paracetamol","warfarin"):     ("LOW","High doses of paracetamol can enhance warfarin effect."),
    ("furosemide","nsaids"):        ("MOD","NSAIDs reduce diuretic effectiveness."),
    ("oxytocin","vasoconstrictors"):("HIGH","Severe hypertension risk."),
}

@login_required
def check_drug_interactions(request):
    """AJAX endpoint — checks for interactions between a list of drug names."""
    drugs_raw = request.GET.get('drugs', '')
    drugs = [d.strip().lower() for d in drugs_raw.split(',') if d.strip()]
    found = []
    for i, d1 in enumerate(drugs):
        for d2 in drugs[i+1:]:
            for (a, b), (severity, message) in INTERACTIONS.items():
                if (a in d1 or a in d2) and (b in d1 or b in d2):
                    found.append({
                        'drug1': d1, 'drug2': d2,
                        'severity': severity,
                        'message': message,
                    })
                    break
    return JsonResponse({'interactions': found, 'checked': len(drugs)})
