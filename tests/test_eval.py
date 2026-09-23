from tests.eval_run import run_eval


def test_engine_locked_numbers_via_eval_runner():
    summary = run_eval()
    engines = summary["engines"]
    assert engines["this_month_spend"] == 18420
    assert engines["spend_delta"] == 6240
    assert engines["food_delta"] == 2100
    assert engines["shopping_delta"] == 1850
    assert engines["food_total"] == 4280
    assert engines["swiggy"] == 1840
    assert engines["zomato"] == 1120
