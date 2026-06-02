package com.marketmind.mobile.ui.campaigns

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.AssistChip
import androidx.compose.material3.AssistChipDefaults
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.marketmind.mobile.data.remote.dto.CampaignDto

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun CampaignDetailScreen(
    onBack: () -> Unit,
    viewModel: CampaignDetailViewModel = hiltViewModel(),
) {
    val state by viewModel.uiState.collectAsStateWithLifecycle()
    val snackbarHostState = remember { SnackbarHostState() }
    var showRejectDialog by remember { mutableStateOf(false) }

    LaunchedEffect(Unit) {
        viewModel.events.collect { event ->
            when (event) {
                is CampaignDetailEvent.ShowSnackbar -> snackbarHostState.showSnackbar(event.message)
                CampaignDetailEvent.NavigateBack -> onBack()
            }
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Detalle de campaña") },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Text(
                            text = "←",
                            style = MaterialTheme.typography.titleLarge,
                        )
                    }
                },
            )
        },
        bottomBar = {
            DetailActionsBar(
                state = state,
                onApproveClick = viewModel::approve,
                onRejectClick = { showRejectDialog = true },
            )
        },
        snackbarHost = { SnackbarHost(snackbarHostState) },
    ) { innerPadding ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding),
        ) {
            when (val s = state) {
                CampaignDetailUiState.Loading -> LoadingState()
                is CampaignDetailUiState.Success -> CampaignDetailBody(campaign = s.campaign)
                is CampaignDetailUiState.Error -> ErrorState(
                    message = s.message,
                    onRetry = viewModel::retry,
                )
            }
        }
    }

    if (showRejectDialog) {
        AlertDialog(
            onDismissRequest = { showRejectDialog = false },
            title = { Text("Rechazar campaña") },
            text = {
                Text("¿Seguro que querés rechazar esta campaña? Esta acción no se puede deshacer.")
            },
            confirmButton = {
                TextButton(
                    onClick = {
                        showRejectDialog = false
                        viewModel.reject()
                    },
                    colors = ButtonDefaults.textButtonColors(
                        contentColor = MaterialTheme.colorScheme.error,
                    ),
                ) { Text("Rechazar") }
            },
            dismissButton = {
                TextButton(onClick = { showRejectDialog = false }) {
                    Text("Cancelar")
                }
            },
        )
    }
}

@Composable
private fun DetailActionsBar(
    state: CampaignDetailUiState,
    onApproveClick: () -> Unit,
    onRejectClick: () -> Unit,
) {
    val submitting = (state as? CampaignDetailUiState.Success)?.submitting == true
    val canAct = state is CampaignDetailUiState.Success && !submitting

    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(16.dp),
        horizontalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        OutlinedButton(
            onClick = onRejectClick,
            enabled = canAct,
            colors = ButtonDefaults.outlinedButtonColors(
                contentColor = MaterialTheme.colorScheme.error,
            ),
            modifier = Modifier.weight(1f),
        ) {
            if (submitting) {
                CircularProgressIndicator(
                    strokeWidth = 2.dp,
                    modifier = Modifier.size(18.dp),
                    color = MaterialTheme.colorScheme.error,
                )
            } else {
                Text("Rechazar")
            }
        }
        Button(
            onClick = onApproveClick,
            enabled = canAct,
            modifier = Modifier.weight(1f),
        ) {
            if (submitting) {
                CircularProgressIndicator(
                    strokeWidth = 2.dp,
                    modifier = Modifier.size(18.dp),
                    color = MaterialTheme.colorScheme.onPrimary,
                )
            } else {
                Text("Aprobar")
            }
        }
    }
}

@Composable
private fun LoadingState() {
    Box(
        modifier = Modifier.fillMaxSize(),
        contentAlignment = Alignment.Center,
    ) {
        CircularProgressIndicator()
    }
}

@Composable
private fun ErrorState(message: String, onRetry: () -> Unit) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(24.dp),
        verticalArrangement = Arrangement.Center,
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Text(
            text = "No pudimos cargar la campaña",
            style = MaterialTheme.typography.titleMedium,
            color = MaterialTheme.colorScheme.error,
        )
        Text(
            text = message,
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            textAlign = TextAlign.Center,
            modifier = Modifier.padding(top = 8.dp),
        )
        Button(
            onClick = onRetry,
            modifier = Modifier.padding(top = 16.dp),
        ) {
            Text("Reintentar")
        }
    }
}

@Composable
private fun CampaignDetailBody(campaign: CampaignDto) {
    val scroll = rememberScrollState()
    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(scroll)
            .padding(horizontal = 16.dp, vertical = 12.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        MetadataCard(campaign)
        HorizontalDivider()
        Text(
            text = campaign.textoGenerado
                ?.takeIf { it.isNotBlank() }
                ?: campaign.prompt
                    ?.takeIf { it.isNotBlank() }
                ?: "Sin contenido generado.",
            style = MaterialTheme.typography.bodyLarge,
        )
    }
}

@Composable
private fun MetadataCard(campaign: CampaignDto) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        elevation = CardDefaults.cardElevation(defaultElevation = 2.dp),
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.Top,
            ) {
                Text(
                    text = campaign.titulo.orEmpty().ifBlank { "Sin título" },
                    style = MaterialTheme.typography.titleLarge,
                    fontWeight = FontWeight.SemiBold,
                    modifier = Modifier.weight(1f, fill = false),
                )
                AssistChip(
                    onClick = {},
                    enabled = false,
                    label = { Text(formatEstado(campaign.estado)) },
                    colors = AssistChipDefaults.assistChipColors(
                        disabledLabelColor = MaterialTheme.colorScheme.onSecondaryContainer,
                        disabledContainerColor = MaterialTheme.colorScheme.secondaryContainer,
                    ),
                )
            }

            campaign.clienteNombre?.takeIf { it.isNotBlank() }?.let {
                Text(
                    text = "Cliente: $it",
                    style = MaterialTheme.typography.bodyMedium,
                )
            }

            campaign.plataforma?.takeIf { it.isNotBlank() }?.let {
                Text(
                    text = "Plataforma: $it",
                    style = MaterialTheme.typography.bodyMedium,
                )
            }

            campaign.industria?.takeIf { it.isNotBlank() }?.let {
                Text(
                    text = "Industria: $it",
                    style = MaterialTheme.typography.bodyMedium,
                )
            }

            campaign.fechaCreacion?.let { iso ->
                Text(
                    text = "Creada: ${formatFecha(iso)}",
                    style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.outline,
                )
            }
        }
    }
}
