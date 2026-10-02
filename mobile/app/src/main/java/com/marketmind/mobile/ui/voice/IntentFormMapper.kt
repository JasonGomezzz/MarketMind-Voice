package com.marketmind.mobile.ui.voice

/**
 * Decide qué campos interpretados por el backend se vuelcan al formulario.
 *
 * Lógica pura (sin Android) para poder probarla en JVM. Los campos de lista
 * (industria, tono, plataforma) solo se aceptan si existen como opción en la
 * app; lo demás queda pendiente para que el marketero lo complete.
 */
object IntentFormMapper {

    val CAMPOS = listOf(
        "titulo",
        "cliente_nombre",
        "cliente_email",
        "industria",
        "tono",
        "plataforma",
        "prompt",
    )

    private val ETIQUETAS = mapOf(
        "titulo" to "título",
        "cliente_nombre" to "nombre del cliente",
        "cliente_email" to "email del cliente",
        "industria" to "industria",
        "tono" to "tono",
        "plataforma" to "plataforma",
        "prompt" to "prompt",
    )

    data class Resultado(
        val valores: Map<String, String>,
        val completados: List<String>,
        val pendientes: List<String>,
    ) {
        val pendientesLegibles: List<String> get() = pendientes.map { ETIQUETAS[it] ?: it }
    }

    fun paraFormulario(
        campos: Map<String, String?>?,
        opciones: Map<String, List<String>>,
    ): Resultado {
        val valores = linkedMapOf<String, String>()
        val pendientes = mutableListOf<String>()
        for (campo in CAMPOS) {
            val valor = campos?.get(campo)?.trim().orEmpty()
            val permitidos = opciones[campo]
            if (valor.isNotEmpty() && (permitidos == null || valor in permitidos)) {
                valores[campo] = valor
            } else {
                pendientes += campo
            }
        }
        return Resultado(valores, valores.keys.toList(), pendientes)
    }

    /** Une lo ya escrito con una frase nueva dictada, sin espacios repetidos. */
    fun agregarDictado(previo: String, nuevo: String, maximo: Int = 2000): String =
        "$previo $nuevo".replace(Regex("\\s+"), " ").trim().take(maximo)
}
