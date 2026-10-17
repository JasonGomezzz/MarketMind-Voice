"""El code y el state del OAuth de Meta (y los secretos de la Graph API) no llegan a los logs."""

import logging

from apps.social import log_filters


class TestLogsSinSecretos:
    def test_redacta_code_state_y_secretos_de_la_url(self):
        linea = ('"GET /api/social/meta/callback/?code=AQB123-xyz&state=s3cr3t_abc HTTP/1.1" 302 0 '
                 "client_secret=zzz&access_token=EAAG1&fb_exchange_token=EAAG2")
        limpio = log_filters.redactar(linea)
        for secreto in ("AQB123-xyz", "s3cr3t_abc", "zzz", "EAAG1", "EAAG2"):
            assert secreto not in limpio
        assert "code=[filtrado]" in limpio and "state=[filtrado]" in limpio

    def test_no_toca_parametros_parecidos(self):
        assert log_filters.redactar("status_code=FINISHED&error_code=190") == "status_code=FINISHED&error_code=190"

    def test_filtro_reescribe_el_registro_con_argumentos(self):
        record = logging.LogRecord("django.server", logging.INFO, __file__, 1, '"%s" %s %s',
                                   ("GET /api/social/meta/callback/?code=AQB&state=xyz HTTP/1.1", "302", "0"), None)
        assert log_filters.FiltroSecretosOAuth().filter(record) is True
        assert record.getMessage() == '"GET /api/social/meta/callback/?code=[filtrado]&state=[filtrado] HTTP/1.1" 302 0'

    def test_mensaje_sin_secretos_queda_igual(self):
        record = logging.LogRecord("httpx", logging.INFO, __file__, 1, "HTTP Request: %s", ("GET /health",), None)
        log_filters.FiltroSecretosOAuth().filter(record)
        assert record.args == ("GET /health",)

    def test_instalado_en_los_loggers_que_registran_urls(self):
        for nombre in ("django.server", "gunicorn.access", "httpx"):
            filtros = logging.getLogger(nombre).filters
            assert sum(isinstance(f, log_filters.FiltroSecretosOAuth) for f in filtros) == 1
