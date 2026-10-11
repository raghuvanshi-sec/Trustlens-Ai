from app.agent.query_planner import extract_job_title


def test_extracts_role_from_job_board_heading():
    text = "Full Stack Engineer (1 - 3) Years of experience\nHyderabad, Telangana, India"
    assert extract_job_title(text, "WorkElate") == "Full Stack Engineer"
