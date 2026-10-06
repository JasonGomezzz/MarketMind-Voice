package com.marketmind.mobile.ui.social

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.marketmind.mobile.data.remote.dto.PublicationDto
import com.marketmind.mobile.data.remote.dto.PublicationStatsDto
import com.marketmind.mobile.data.remote.dto.ResumenRedesDto
import com.marketmind.mobile.data.repository.SocialRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.async
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject

data class StatsUiState(
    val cargando: Boolean = true,
    val error: String? = null,
    val resumen: ResumenRedesDto? = null,
    val publicaciones: List<PublicationDto> = emptyList(),
    val actualizando: Boolean = false,
    val mensaje: String? = null,
    val detalle: DetalleUiState? = null,
)

data class DetalleUiState(
    val id: Long,
    val datos: PublicationStatsDto? = null,
    val error: String? = null,
)

/** Estadísticas de Instagram y Facebook. Django decide qué ve cada rol. */
@HiltViewModel
class StatsViewModel @Inject constructor(
    private val repository: SocialRepository,
) : ViewModel() {

    private val _uiState = MutableStateFlow(StatsUiState())
    val uiState: StateFlow<StatsUiState> = _uiState.asStateFlow()

    init {
        cargar()
    }

    fun cargar() {
        viewModelScope.launch {
            _uiState.update { it.copy(cargando = it.resumen == null, error = null) }
            val resumen = async { repository.resumen() }
            val lista = async { repository.publicaciones() }
            val r = resumen.await()
            val l = lista.await()
            val error = r.exceptionOrNull() ?: l.exceptionOrNull()
            _uiState.update {
                if (error != null) {
                    it.copy(cargando = false, error = error.message ?: "No se pudieron cargar las estadísticas.")
                } else {
                    it.copy(cargando = false, resumen = r.getOrNull(), publicaciones = l.getOrNull().orEmpty())
                }
            }
        }
    }

    /** Pide a Django que lea de Meta las publicaciones recientes (respeta 10 min por publicación). */
    fun actualizarMetricas() {
        if (_uiState.value.actualizando) return
        viewModelScope.launch {
            _uiState.update { it.copy(actualizando = true, mensaje = null) }
            repository.actualizarMetricas()
                .onSuccess { r ->
                    val texto = if (r.actualizadas == 0) "No hay publicaciones para actualizar." else
                        "Métricas al día (${r.actualizadas} ${if (r.actualizadas == 1) "publicación" else "publicaciones"})."
                    _uiState.update { it.copy(actualizando = false, mensaje = texto) }
                    cargar()
                }
                .onFailure { e ->
                    _uiState.update { it.copy(actualizando = false, mensaje = e.message ?: "No se pudieron actualizar las métricas.") }
                }
        }
    }

    fun abrir(id: Long) {
        _uiState.update { it.copy(detalle = DetalleUiState(id = id)) }
        viewModelScope.launch {
            repository.estadisticas(id)
                .onSuccess { datos ->
                    _uiState.update { estado ->
                        val detalle = estado.detalle?.takeIf { it.id == id } ?: return@update estado
                        estado.copy(
                            detalle = detalle.copy(datos = datos),
                            // La fila muestra la cifra recién traída de Meta.
                            publicaciones = estado.publicaciones.map { p ->
                                if (p.id == id) p.copy(ultimaMetrica = datos.publicacion.ultimaMetrica) else p
                            },
                        )
                    }
                }
                .onFailure { e ->
                    _uiState.update { estado ->
                        val detalle = estado.detalle?.takeIf { it.id == id } ?: return@update estado
                        estado.copy(detalle = detalle.copy(error = e.message ?: "No se pudieron cargar las estadísticas."))
                    }
                }
        }
    }

    fun cerrarDetalle() {
        _uiState.update { it.copy(detalle = null) }
    }
}
