package com.marketmind.mobile.ui.campaigns

internal fun formatEstado(raw: String): String =
    raw.replace('_', ' ').replaceFirstChar { it.uppercase() }

internal fun formatFecha(iso: String): String =
    iso.take(10).let { date ->
        runCatching {
            val (y, m, d) = date.split("-")
            "$d/$m/$y"
        }.getOrDefault(date)
    }
