import pytest

from project.sentry import DEFAULT_TRACES_SAMPLE_RATE, POLLED_TRACES_SAMPLE_RATE, traces_sampler


def _request(path, method="GET"):
    return {"wsgi_environ": {"PATH_INFO": path, "REQUEST_METHOD": method}}


class TestTracesSampler:
    @pytest.mark.parametrize(
        "path",
        [
            "/health/",
            "/version/",
            "/update/check/",
            "/users/42/picture/0da9f3124c537323246f48b3ee37be97687a9c673eacca9ab4f316b968c058cc",
            "/variants/classical/nations/england/flag/abc123.svg",
        ],
    )
    def test_infrastructure_and_asset_requests_are_never_traced(self, path):
        assert traces_sampler(_request(path)) == 0

    @pytest.mark.parametrize("path", ["/game/the-match-1a2b/", "/games/the-match-1a2b/channels/"])
    def test_polled_reads_are_sampled_at_the_polled_rate(self, path):
        assert traces_sampler(_request(path)) == POLLED_TRACES_SAMPLE_RATE

    def test_writes_to_a_polled_path_are_sampled_at_the_default_rate(self):
        assert traces_sampler(_request("/games/the-match-1a2b/channels/", method="POST")) == DEFAULT_TRACES_SAMPLE_RATE

    def test_nested_game_reads_are_sampled_at_the_default_rate(self):
        assert traces_sampler(_request("/game/the-match-1a2b/orders/")) == DEFAULT_TRACES_SAMPLE_RATE

    def test_transactions_outside_a_request_are_sampled_at_the_default_rate(self):
        assert traces_sampler({"transaction_context": {"name": "task"}}) == DEFAULT_TRACES_SAMPLE_RATE
