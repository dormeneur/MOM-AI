"""
MeetMind Demo — Synthetic Meeting Pipeline Demonstration

Feeds a realistic meeting transcript (from demo_config.json) through:
  1. Feature Engineering (TF-IDF + handcrafted)
  2. Sentence Classification (Perceptron vs KNN vs MLP)
  3. Named Entity Recognition (BERT NER)
  4. Abstractive Summarisation (BART)
  5. Minutes of Meeting Generation (HTML)
  6. Email Dispatch (personalised MOMs to each participant)

Edit demo_config.json to change participants, emails, or the conversation.

Run:  python -m demo
"""

import os
import sys
import json
import joblib
import numpy as np

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# ── Load config ──────────────────────────────────────────────────────────────

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "demo_config.json")


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


# ── Colours / formatting ────────────────────────────────────────────────────

C = {
    "H": "\033[95m", "B": "\033[94m", "C": "\033[96m", "G": "\033[92m",
    "Y": "\033[93m", "R": "\033[91m", "BOLD": "\033[1m", "DIM": "\033[2m",
    "END": "\033[0m",
}

LABEL_STYLE = {
    "action_item":      (C["R"],  "[ACTION]"),
    "decision":         (C["B"],  "[DECISION]"),
    "topic":            (C["C"],  "[TOPIC]"),
    "deadline_mention": (C["Y"],  "[DEADLINE]"),
    "general":          (C["DIM"],"[GENERAL]"),
}


def banner(text):
    print(f"\n{'=' * 72}")
    print(f"{C['BOLD']}{C['H']}  {text}{C['END']}")
    print(f"{'=' * 72}\n")


def section(text):
    print(f"\n{C['BOLD']}  -- {text} --{C['END']}\n")


def table(headers, rows):
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(str(cell)))
    sep = "  +" + "+".join("-" * (w + 2) for w in widths) + "+"
    hdr = "  |" + "|".join(f" {C['BOLD']}{h:<{w}}{C['END']} " for h, w in zip(headers, widths)) + "|"
    fmt = "  |" + "|".join(f" {{:<{w}}} " for w in widths) + "|"
    print(sep)
    print(hdr)
    print(sep)
    for row in rows:
        print(fmt.format(*[str(c) for c in row]))
    print(sep)


def wrap(text, w=65):
    words, lines, cur, ln = text.split(), [], [], 0
    for word in words:
        if ln + len(word) + 1 > w:
            lines.append(" ".join(cur))
            cur, ln = [word], len(word)
        else:
            cur.append(word)
            ln += len(word) + 1
    if cur:
        lines.append(" ".join(cur))
    return lines


# ── Main ─────────────────────────────────────────────────────────────────────

def run_demo():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # Load .env for SMTP
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    config = load_config()
    meeting = config["meeting"]
    participants = config["participants"]
    transcript = config["transcript"]

    sentences = [s["text"] for s in transcript]
    speakers = [s["speaker"] for s in transcript]
    name_to_email = {p["display_name"]: p["email"] for p in participants}

    banner("MeetMind -- ML Pipeline Demonstration")
    print(f"  Meeting:      {meeting['title']}")
    print(f"  Date:         {meeting['date']}")
    print(f"  Participants: {', '.join(p['display_name'] for p in participants)}")
    print(f"  Sentences:    {len(sentences)}")
    print(f"  Config file:  demo_config.json (editable)")

    # ── STEP 1: Feature Engineering ──────────────────────────────────────────
    banner("STEP 1 -- Feature Engineering (TF-IDF + Handcrafted)")

    from ml.classifier.features import extract_features

    print("  Extracting 517-dimensional feature vectors...")
    print("    [0-511]  TF-IDF unigram+bigram features")
    print("    [512]    has_modal_verb (will/shall/should/must)")
    print("    [513]    has_person_name (Title Case token)")
    print("    [514]    is_imperative (starts with verb)")
    print("    [515]    has_deadline_word (monday/friday/by/before)")
    print("    [516]    sentence_length (normalised)")
    print()

    features = extract_features(sentences, training=False)
    print(f"  Feature matrix: {features.shape}  ({len(sentences)} sentences x 517 features)")

    section("Sample Features")
    samples = [0, 5, 13, 17]
    for i in samples:
        if i >= len(sentences):
            continue
        f = features[i, 512:]
        short = sentences[i][:60] + ("..." if len(sentences[i]) > 60 else "")
        print(f'  "{short}"')
        print(f"     modal={int(f[0])} name={int(f[1])} imperative={int(f[2])} deadline={int(f[3])} len={f[4]:.2f}")
        print()

    # ── STEP 2: Classification ───────────────────────────────────────────────
    banner("STEP 2 -- Sentence Classification (3 Models)")

    from ml.classifier.mlp_model import INT_TO_LABEL

    print("  Loading models...")
    perceptron = joblib.load("ml/classifier/models/perceptron_classifier.pkl")
    knn = joblib.load("ml/classifier/models/knn_classifier.pkl")
    mlp = joblib.load("ml/classifier/models/mlp_classifier.pkl")
    print(f"  Perceptron  : binary (action_item vs rest)")
    print(f"  KNN (k=5)   : 5-class, instance-based")
    print(f"  MLP 256-128 : 5-class, neural network [PRIMARY]")

    perc_preds = perceptron.predict(features)
    perc_labels = ["action_item" if p == 1 else "not_action" for p in perc_preds]
    knn_preds = knn.predict(features)
    knn_labels = [INT_TO_LABEL[p] for p in knn_preds]
    mlp_labels = mlp.predict(features)
    mlp_proba = mlp.predict_proba(features)

    section("Classification Results")

    rows = []
    for i in range(len(sentences)):
        short = sentences[i][:42] + ("..." if len(sentences[i]) > 42 else "")
        conf = f"{mlp_proba[i].max():.0%}"
        rows.append([short, perc_labels[i][:12], knn_labels[i][:14], mlp_labels[i][:14], conf])

    table(["Sentence", "Perceptron", "KNN (k=5)", "MLP [Primary]", "Conf"], rows)

    section("Counts")
    for label in ["action_item", "decision", "topic", "deadline_mention", "general"]:
        count = sum(1 for l in mlp_labels if l == label)
        color, tag = LABEL_STYLE[label]
        print(f"  {color}{tag:<14}{C['END']}  {count}")

    # ── STEP 3: NER ──────────────────────────────────────────────────────────
    banner("STEP 3 -- Task Extraction (BERT NER)")

    print("  Model: dslim/bert-base-NER (Transfer Learning)")
    print("  Concept: BERT pre-trained on BookCorpus + Wikipedia,")
    print("           fine-tuned on CoNLL-2003 NER dataset")
    print("  Extracts: PERSON (assignee), DATE/TIME (deadline), ACTION VERB")
    print()

    from ml.ner.task_extractor import TaskExtractor
    extractor = TaskExtractor()

    action_items = []
    for i in range(len(sentences)):
        if mlp_labels[i] in ("action_item", "deadline_mention"):
            result = extractor.extract(sentences[i], speaker_name=speakers[i])
            result["sentence"] = sentences[i]
            result["speaker"] = speakers[i]
            result["label"] = mlp_labels[i]
            action_items.append(result)

    section(f"Extracted Tasks ({len(action_items)})")

    for idx, item in enumerate(action_items, 1):
        color, tag = LABEL_STYLE.get(item["label"], (C["DIM"], "[?]"))
        print(f"  {color}Task {idx}{C['END']}: {tag}")
        print(f"     \"{item['sentence'][:70]}\"")
        print(f"     Assignee:   {item['assignee'] or 'Unassigned'}")
        print(f"     Deadline:   {item['deadline'] or 'None'}")
        print(f"     Verb:       {item['task_verb'] or 'N/A'}")
        print(f"     Confidence: {item['confidence']:.0%}")
        print()

    # ── STEP 4: Summarisation ────────────────────────────────────────────────
    banner("STEP 4 -- Abstractive Summarisation (BART)")

    print("  Model: sshleifer/distilbart-cnn-12-6 (Seq2Seq)")
    print("  Encoder reads full transcript, Decoder generates summary.")
    print("  Beam search (k=4) for optimal decoding.")
    print()

    full_transcript = "\n".join(f"{s}: {t}" for s, t in zip(speakers, sentences))

    try:
        from ml.summariser.summariser import MeetingSummariser
        print("  Generating... (10-20 sec on CPU)")
        summariser = MeetingSummariser()
        summary = summariser.summarise(full_transcript)
        print(f"\n  Summary:")
        for line in wrap(summary):
            print(f"     {line}")
    except Exception as e:
        summary = (
            f"The team reviewed progress on the MeetMind capstone project. "
            f"Key updates include completion of the ML classifier pipeline with Perceptron, KNN, and MLP models, "
            f"progress on BERT NER for task extraction, and BART-based summarisation. "
            f"Several action items were assigned with deadlines for the upcoming presentation."
        )
        print(f"  (Summariser unavailable: {e})")
        print(f"\n  Using fallback summary:")
        for line in wrap(summary):
            print(f"     {line}")

    # ── STEP 5: MOM Generation ───────────────────────────────────────────────
    banner("STEP 5 -- Minutes of Meeting (MOM) Generation")

    from mom.generator import MOMGenerator
    gen = MOMGenerator()

    decisions = [
        {"speaker": speakers[i], "text": sentences[i]}
        for i in range(len(sentences)) if mlp_labels[i] == "decision"
    ]
    topics = [
        {"speaker": speakers[i], "text": sentences[i]}
        for i in range(len(sentences)) if mlp_labels[i] == "topic"
    ]
    ai_list = [
        {
            "task_description": item["task_description"],
            "assigned_to_name": item["assignee"],
            "assigned_to_email": name_to_email.get(item["assignee"]),
            "assigned_by_name": item["speaker"],
            "deadline": item["deadline"],
            "confidence": item["confidence"],
        }
        for item in action_items
    ]

    global_html = gen.generate_global(
        summary=summary,
        decisions=decisions,
        topics=topics,
        action_items=ai_list,
        participants=participants,
    )

    os.makedirs("demo_output", exist_ok=True)
    with open("demo_output/mom_global.html", "w", encoding="utf-8") as f:
        f.write(global_html)
    print(f"  Saved: demo_output/mom_global.html")

    personalised_moms = {}
    for p in participants:
        p_tasks = [
            t for t in ai_list
            if t.get("assigned_to_name") and (
                p["display_name"] in (t["assigned_to_name"] or "")
                or p["display_name"].split()[0] in (t["assigned_to_name"] or "")
            )
        ]
        p_html = gen.generate_personalised(
            participant=p,
            summary=summary,
            decisions=decisions,
            topics=topics,
            tasks=p_tasks,
        )
        fname = p["display_name"].replace(" ", "_").lower()
        path = f"demo_output/mom_{fname}.html"
        with open(path, "w", encoding="utf-8") as f:
            f.write(p_html)
        print(f"  Saved: {path}  ({len(p_tasks)} tasks for {p['display_name']})")
        personalised_moms[p["email"]] = {"html": p_html, "name": p["display_name"], "tasks": len(p_tasks)}

    print(f"\n  Open demo_output/mom_global.html in your browser to preview.")

    # ── STEP 6: Email Dispatch ───────────────────────────────────────────────
    banner("STEP 6 -- Email Dispatch")

    smtp_user = os.environ.get("SMTP_USER", "")
    smtp_pass = os.environ.get("SMTP_PASSWORD", "")

    if not smtp_user or not smtp_pass:
        print(f"  {C['Y']}SMTP not configured.{C['END']}")
        print(f"  To enable email, set in .env:")
        print(f"    SMTP_USER=your_gmail@gmail.com")
        print(f"    SMTP_PASSWORD=your_app_password")
        print(f"\n  Skipping email dispatch. MOMs are saved in demo_output/")
    else:
        from mom.mailer import Mailer
        mailer = Mailer()

        print(f"  Sending from: {smtp_user}")
        print()

        # Send personalised MOMs to each participant
        for email, data in personalised_moms.items():
            subject = f"[MeetMind] Your action items from {meeting['title']}"
            try:
                mailer.send(email, subject, data["html"])
                print(f"  {C['G']}SENT{C['END']}  {email}  ({data['tasks']} tasks)")
            except Exception as e:
                print(f"  {C['R']}FAIL{C['END']}  {email}  ({e})")

        # Send global MOM to first participant (host)
        host_email = participants[0]["email"]
        try:
            mailer.send(host_email, f"[MeetMind] Full MOM -- {meeting['title']}", global_html)
            print(f"  {C['G']}SENT{C['END']}  {host_email}  (Global MOM)")
        except Exception as e:
            print(f"  {C['R']}FAIL{C['END']}  {host_email}  (Global: {e})")

        print(f"\n  {C['G']}All emails dispatched!{C['END']}")

    # ── Summary ──────────────────────────────────────────────────────────────
    banner("Pipeline Summary")

    print(f"  Sentences classified:   {len(sentences)}")
    print(f"  Action items:           {sum(1 for l in mlp_labels if l == 'action_item')}")
    print(f"  Decisions:              {sum(1 for l in mlp_labels if l == 'decision')}")
    print(f"  Topics:                 {sum(1 for l in mlp_labels if l == 'topic')}")
    print(f"  Deadlines:              {sum(1 for l in mlp_labels if l == 'deadline_mention')}")
    print(f"  Tasks extracted (NER):  {len(action_items)}")
    print(f"  MOMs generated:         {len(personalised_moms) + 1}")
    print(f"  Emails sent:            {'Yes' if smtp_user and smtp_pass else 'No (configure .env)'}")
    print()

    section("ML Concepts Used")
    table(
        ["Concept", "Where", "Purpose"],
        [
            ["Perceptron", "perceptron_model.py", "Binary baseline classifier"],
            ["KNN (k=5)", "knn_model.py", "Instance-based 5-class"],
            ["MLP (Backprop)", "mlp_model.py", "Primary neural classifier"],
            ["TF-IDF", "features.py", "Text to numeric vectors"],
            ["Transfer Learning", "task_extractor.py", "BERT NER (pre-trained)"],
            ["Seq2Seq + Beam", "summariser.py", "BART summarisation"],
            ["Softmax", "mlp_model.py", "Probability distribution"],
        ],
    )

    print(f"\n  {'=' * 72}")
    print(f"  {C['G']}{C['BOLD']}  Demo complete!{C['END']}")
    print(f"  {'=' * 72}\n")


if __name__ == "__main__":
    run_demo()
