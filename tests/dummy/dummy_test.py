import pytest


class TestDummy:
    @pytest.mark.parametrize(
        'test_input_a, test_input_b, expected',
        [
            (2, 2, 4),
            (0, 5, 0),
        ]
    )
    def test_int_multiply(self, test_input_a, test_input_b, expected):
        assert test_input_a * test_input_b == expected
