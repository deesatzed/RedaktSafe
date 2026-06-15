from redaktsafe.cli import main


def test_doctor_exits_zero(capsys):
    assert main(["doctor"]) == 0
    output = capsys.readouterr().out
    assert '"status": "ok"' in output
    assert '"network_required": false' in output

