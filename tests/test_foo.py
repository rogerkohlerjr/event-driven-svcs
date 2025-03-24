from event_driven_svcs.foo import foo


def test_foo():
    assert foo("foo") == "foo"
