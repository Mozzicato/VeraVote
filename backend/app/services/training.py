"""Training modules and assessment (PRD §4.4, §4.5). Content is a condensed MVP version."""
from ..config import ASSESSMENT_PASS_MARK

MODULES = [
    {
        "id": "m1", "title": "Understanding Nigerian elections",
        "points": [
            "Elections are organised from state to LGA to ward (registration area) to polling unit.",
            "INEC officials run the polling unit; the Presiding Officer completes and announces the result form.",
            "Accredited observers watch the process. Party agents represent parties. Neither runs the election.",
            "VeraVote training does not make you an INEC-accredited observer.",
        ],
    },
    {
        "id": "m2", "title": "Election observation ethics",
        "points": [
            "Stay neutral. Do not campaign, wear party colours or tell voters how to vote.",
            "Never interfere with voting, counting or officials' work.",
            "Your safety comes first. Leave if you feel threatened; you can withdraw at any time.",
            "Respect voters' privacy. Never photograph how someone voted.",
        ],
    },
    {
        "id": "m3", "title": "Result documentation",
        "points": [
            "Form EC8A records the polling-unit result for each contest.",
            "Check the polling-unit name and code at the top of the form.",
            "Candidate votes added together should equal total valid votes.",
            "Total valid votes plus rejected votes should equal total votes cast.",
            "Note forms that are incomplete, altered or hard to read. Do not guess figures.",
        ],
    },
    {
        "id": "m4", "title": "Evidence collection",
        "points": [
            "Photograph the whole form, flat, in good light, with all four corners visible.",
            "Only photograph forms that are publicly displayed or that you are permitted to see.",
            "Do not edit, filter or crop the photo. Submit the original.",
            "Never block officials or voters to get a photo.",
        ],
    },
    {
        "id": "m5", "title": "Using VeraVote",
        "points": [
            "You can capture evidence offline. It is saved on your phone until you have signal.",
            "Your submission is only 'received' once the server sends you a receipt.",
            "The time your phone shows is recorded as device-reported, not verified.",
            "Use the safety button to withdraw or report a threat at any time.",
        ],
    },
]

# Each question: knowledge, practical result-sheet reading, or simulated submission exercise.
QUESTIONS = [
    {"id": "q1", "kind": "knowledge", "text": "Who completes and announces the polling-unit result?",
     "options": ["The Presiding Officer (INEC)", "The most senior party agent", "A VeraVote volunteer"], "answer": 0},
    {"id": "q2", "kind": "knowledge", "text": "Does completing VeraVote training make you an INEC-accredited observer?",
     "options": ["Yes", "No, accreditation is a separate INEC process"], "answer": 1},
    {"id": "q3", "kind": "knowledge", "text": "A party agent asks you to leave the polling unit and you feel unsafe. What should you do?",
     "options": ["Argue until they back down", "Leave and use the safety button to report it", "Hide and keep filming"], "answer": 1},
    {"id": "q4", "kind": "knowledge", "text": "Which of these may you photograph?",
     "options": ["A voter's marked ballot", "The completed result form displayed for the public", "The inside of a voting cubicle"], "answer": 1},
    {"id": "q5", "kind": "practical",
     "text": "Simulated EC8A: Candidate A 120, Candidate B 85, Candidate C 40. What should total valid votes be?",
     "options": ["205", "245", "250"], "answer": 1},
    {"id": "q6", "kind": "practical",
     "text": "Simulated EC8A: total valid votes 245, rejected votes 5. What should total votes cast be?",
     "options": ["240", "245", "250"], "answer": 2},
    {"id": "q7", "kind": "practical",
     "text": "The form shows total votes cast 260 but only 250 voters accredited. What do you do?",
     "options": ["Correct the figure before submitting", "Submit the photo as-is; the system flags it for review", "Do not submit it"], "answer": 1},
    {"id": "q8", "kind": "practical", "text": "One candidate's figure is smudged and unreadable. What do you do?",
     "options": ["Guess a likely figure", "Submit the original photo and note that the figure is unreadable", "Ask a party agent for the number"], "answer": 1},
    {"id": "q9", "kind": "exercise", "text": "You captured a photo with no signal. When is it officially received?",
     "options": ["When I take the photo", "When the server sends me a receipt after syncing", "When I press save"], "answer": 1},
    {"id": "q10", "kind": "exercise", "text": "Your photo looks dark. Before submitting you should:",
     "options": ["Brighten it with a filter app", "Retake it if safe, and submit the original file", "Crop out the edges"], "answer": 1},
]


def public_questions() -> list[dict]:
    return [{k: v for k, v in q.items() if k != "answer"} for q in QUESTIONS]


def score(answers: dict[str, int]) -> tuple[float, bool, list[str]]:
    """Returns (score 0..1, passed, ids of incorrect questions)."""
    wrong = [q["id"] for q in QUESTIONS if answers.get(q["id"]) != q["answer"]]
    s = (len(QUESTIONS) - len(wrong)) / len(QUESTIONS)
    return s, s >= ASSESSMENT_PASS_MARK, wrong
