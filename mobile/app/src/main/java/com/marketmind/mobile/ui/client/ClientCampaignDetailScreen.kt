package com.marketmind.mobile.ui.client

import android.graphics.BitmapFactory
import android.util.Base64
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.ModalBottomSheet
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.rememberModalBottomSheetState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.marketmind.mobile.data.remote.dto.CampaignDto
import com.marketmind.mobile.ui.campaigns.formatEstado
import com.marketmind.mobile.ui.campaigns.formatFecha

private val BrandBlue = Color(0xFF4D4AF0)
private val PageBackground = Color(0xFFFCF9FF)
private val TextDark = Color(0xFF12132A)
private val TextMuted = Color(0xFF74778A)
private val DangerRed = Color(0xFFD73737)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ClientCampaignDetailScreen(
    onBack: () -> Unit,
    viewModel: ClientCampaignDetailViewModel = hiltViewModel(),
) {
    val state by viewModel.uiState.collectAsStateWithLifecycle()
    val snackbarHostState = remember { SnackbarHostState() }
    var showRejectSheet by remember { mutableStateOf(false) }
    var feedbackText by remember { mutableStateOf("") }

    LaunchedEffect(Unit) {
        viewModel.events.collect { event ->
            when (event) {
                is ClientCampaignDetailEvent.ShowSnackbar -> snackbarHostState.showSnackbar(event.message)
                ClientCampaignDetailEvent.NavigateBack -> onBack()
            }
        }
    }

    Scaffold(
        containerColor = PageBackground,
        topBar = {
            ClientDetailTopBar(onBack = onBack)
        },
        bottomBar = {
            DetailActionsBar(
                state = state,
                onApproveClick = viewModel::approve,
                onRejectClick = { showRejectSheet = true },
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
                ClientCampaignDetailUiState.Loading -> LoadingState()
                is ClientCampaignDetailUiState.Success -> CampaignDetailBody(campaign = s.campaign)
                is ClientCampaignDetailUiState.Error -> ErrorState(
                    message = s.message,
                    onRetry = viewModel::retry,
                )
            }
        }
    }

    if (showRejectSheet) {
        RejectFeedbackSheet(
            feedbackText = feedbackText,
            onFeedbackChange = { if (it.length <= 500) feedbackText = it },
            onDismiss = {
                showRejectSheet = false
                feedbackText = ""
            },
            onConfirm = { feedback ->
                viewModel.reject(feedback)
                showRejectSheet = false
                feedbackText = ""
            },
        )
    }
}

@Composable
private fun ClientDetailTopBar(onBack: () -> Unit) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .background(Color.White.copy(alpha = 0.82f))
            .statusBarsPadding()
            .padding(horizontal = 12.dp, vertical = 10.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Surface(
            onClick = onBack,
            shape = CircleShape,
            color = Color.Transparent,
            modifier = Modifier.size(36.dp),
        ) {
            Box(contentAlignment = Alignment.Center) {
                Icon(
                    imageVector = Icons.Filled.ArrowBack,
                    contentDescription = "Volver",
                    tint = BrandBlue,
                    modifier = Modifier.size(22.dp),
                )
            }
        }
        Text(
            text = "Detalle de campaña",
            color = TextDark,
            fontSize = 17.sp,
            fontWeight = FontWeight.ExtraBold,
            maxLines = 1,
            overflow = TextOverflow.Ellipsis,
            modifier = Modifier
                .weight(1f)
                .padding(horizontal = 8.dp),
        )
    }
}

@Composable
private fun DetailActionsBar(
    state: ClientCampaignDetailUiState,
    onApproveClick: () -> Unit,
    onRejectClick: () -> Unit,
) {
    val submitting = (state as? ClientCampaignDetailUiState.Success)?.submitting == true
    val canAct = state is ClientCampaignDetailUiState.Success && !submitting

    Row(
        modifier = Modifier
            .fillMaxWidth()
            .background(Color.White.copy(alpha = 0.92f))
            .navigationBarsPadding()
            .padding(16.dp),
        horizontalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        OutlinedButton(
            onClick = onRejectClick,
            enabled = canAct,
            shape = RoundedCornerShape(10.dp),
            border = BorderStroke(1.dp, DangerRed),
            colors = ButtonDefaults.outlinedButtonColors(contentColor = DangerRed),
            modifier = Modifier.weight(1f),
        ) {
            if (submitting) {
                CircularProgressIndicator(
                    strokeWidth = 2.dp,
                    modifier = Modifier.size(18.dp),
                    color = DangerRed,
                )
            } else {
                Text("Rechazar", fontWeight = FontWeight.ExtraBold)
            }
        }
        Button(
            onClick = onApproveClick,
            enabled = canAct,
            shape = RoundedCornerShape(10.dp),
            colors = ButtonDefaults.buttonColors(containerColor = BrandBlue),
            modifier = Modifier.weight(1f),
        ) {
            if (submitting) {
                CircularProgressIndicator(
                    strokeWidth = 2.dp,
                    modifier = Modifier.size(18.dp),
                    color = Color.White,
                )
            } else {
                Text("Aprobar", color = Color.White, fontWeight = FontWeight.ExtraBold)
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
        CircularProgressIndicator(color = BrandBlue)
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
            color = TextDark,
            fontSize = 18.sp,
            fontWeight = FontWeight.ExtraBold,
            textAlign = TextAlign.Center,
        )
        Text(
            text = message,
            color = TextMuted,
            fontSize = 14.sp,
            textAlign = TextAlign.Center,
            modifier = Modifier.padding(top = 8.dp),
        )
        Button(
            onClick = onRetry,
            colors = ButtonDefaults.buttonColors(containerColor = BrandBlue),
            shape = RoundedCornerShape(10.dp),
            modifier = Modifier.padding(top = 16.dp),
        ) {
            Text("Reintentar", color = Color.White, fontWeight = FontWeight.Bold)
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
        verticalArrangement = Arrangement.spacedBy(14.dp),
    ) {
        MetadataCard(campaign)

        CampaignImage(campaign)

        Card(
            modifier = Modifier.fillMaxWidth(),
            shape = RoundedCornerShape(12.dp),
            colors = CardDefaults.cardColors(containerColor = Color.White),
            elevation = CardDefaults.cardElevation(defaultElevation = 2.dp),
            border = BorderStroke(1.dp, Color(0xFFEDEAF6)),
        ) {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(16.dp),
                verticalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                Text(
                    text = "TEXTO GENERADO",
                    color = Color(0xFF7B74F2),
                    fontSize = 12.sp,
                    fontWeight = FontWeight.ExtraBold,
                    letterSpacing = 1.sp,
                )
                Text(
                    text = campaign.textoGenerado
                        ?.takeIf { it.isNotBlank() }
                        ?: campaign.prompt
                            ?.takeIf { it.isNotBlank() }
                        ?: "Sin contenido generado.",
                    color = Color(0xFF4A4D66),
                    fontSize = 15.sp,
                    lineHeight = 22.sp,
                    fontWeight = FontWeight.Medium,
                )
            }
        }

        campaign.feedbackRechazo?.takeIf { it.isNotBlank() }?.let { feedback ->
            Card(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(12.dp),
                colors = CardDefaults.cardColors(containerColor = Color(0xFFFFF1F1)),
                elevation = CardDefaults.cardElevation(defaultElevation = 0.dp),
                border = BorderStroke(1.dp, Color(0xFFF3C9C9)),
            ) {
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(16.dp),
                    verticalArrangement = Arrangement.spacedBy(6.dp),
                ) {
                    Text(
                        text = "MOTIVO DEL RECHAZO",
                        color = DangerRed,
                        fontSize = 12.sp,
                        fontWeight = FontWeight.ExtraBold,
                        letterSpacing = 1.sp,
                    )
                    Text(
                        text = feedback,
                        color = Color(0xFF7A2E2E),
                        fontSize = 14.sp,
                        lineHeight = 20.sp,
                        fontWeight = FontWeight.Medium,
                    )
                }
            }
        }
    }
}

@Composable
private fun MetadataCard(campaign: CampaignDto) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(12.dp),
        colors = CardDefaults.cardColors(containerColor = Color.White),
        elevation = CardDefaults.cardElevation(defaultElevation = 2.dp),
        border = BorderStroke(1.dp, Color(0xFFEDEAF6)),
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
                    color = TextDark,
                    fontSize = 20.sp,
                    lineHeight = 24.sp,
                    fontWeight = FontWeight.ExtraBold,
                    modifier = Modifier.weight(1f, fill = false),
                )
                StatePill(campaign.estado)
            }

            campaign.clienteNombre?.takeIf { it.isNotBlank() }?.let {
                MetaRow(label = "Cliente", value = it)
            }
            campaign.plataforma?.takeIf { it.isNotBlank() }?.let {
                MetaRow(label = "Plataforma", value = it)
            }
            campaign.industria?.takeIf { it.isNotBlank() }?.let {
                MetaRow(label = "Industria", value = it)
            }
            campaign.fechaCreacion?.let { iso ->
                MetaRow(label = "Creada", value = formatFecha(iso))
            }
        }
    }
}

@Composable
private fun MetaRow(label: String, value: String) {
    Row(modifier = Modifier.fillMaxWidth()) {
        Text(
            text = "$label: ",
            color = TextMuted,
            fontSize = 14.sp,
            fontWeight = FontWeight.SemiBold,
        )
        Text(
            text = value,
            color = TextDark,
            fontSize = 14.sp,
            fontWeight = FontWeight.SemiBold,
        )
    }
}

@Composable
private fun CampaignImage(campaign: CampaignDto) {
    val imagenB64 = campaign.imagenB64?.takeIf { it.isNotBlank() }
    if (imagenB64 != null) {
        val imageBytes = runCatching { Base64.decode(imagenB64, Base64.DEFAULT) }.getOrNull()
        val bitmap = imageBytes?.let { BitmapFactory.decodeByteArray(it, 0, it.size) }
        if (bitmap != null) {
            Image(
                bitmap = bitmap.asImageBitmap(),
                contentDescription = "Imagen generada",
                modifier = Modifier
                    .fillMaxWidth()
                    .clip(RoundedCornerShape(12.dp)),
                contentScale = ContentScale.FillWidth,
            )
            return
        }
    }
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(12.dp),
        colors = CardDefaults.cardColors(containerColor = Color.White),
        elevation = CardDefaults.cardElevation(defaultElevation = 0.dp),
        border = BorderStroke(1.dp, Color(0xFFEDEAF6)),
    ) {
        Text(
            text = "Imagen no generada aún",
            color = TextMuted,
            fontSize = 14.sp,
            fontWeight = FontWeight.SemiBold,
            modifier = Modifier.padding(16.dp),
        )
    }
}

@Composable
private fun StatePill(estado: String) {
    val (fg, bg) = when (estado) {
        "aprobado" -> Color(0xFF087A44) to Color(0xFFCFF8E4)
        "rechazado" -> DangerRed to Color(0xFFFFE0E0)
        "pendiente_aprobacion" -> Color(0xFFA76525) to Color(0xFFF3E0C8)
        "generado" -> BrandBlue to Color(0xFFE8E7FF)
        else -> TextMuted to Color(0xFFECEAF5)
    }
    Text(
        text = formatEstado(estado),
        color = fg,
        fontSize = 10.sp,
        fontWeight = FontWeight.ExtraBold,
        modifier = Modifier
            .clip(RoundedCornerShape(14.dp))
            .background(bg)
            .padding(horizontal = 10.dp, vertical = 5.dp),
        maxLines = 1,
    )
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun RejectFeedbackSheet(
    feedbackText: String,
    onFeedbackChange: (String) -> Unit,
    onDismiss: () -> Unit,
    onConfirm: (String) -> Unit,
) {
    val sheetState = rememberModalBottomSheetState(skipPartiallyExpanded = true)
    val isValid = feedbackText.trim().length in 10..500

    ModalBottomSheet(
        onDismissRequest = onDismiss,
        sheetState = sheetState,
        containerColor = Color.White,
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 16.dp, vertical = 16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            Text(
                text = "Motivo del rechazo",
                color = TextDark,
                fontSize = 18.sp,
                fontWeight = FontWeight.ExtraBold,
            )
            Text(
                text = "Explica al marketero por qué rechazas esta campaña (mínimo 10 caracteres).",
                color = TextMuted,
                fontSize = 13.sp,
            )

            OutlinedTextField(
                value = feedbackText,
                onValueChange = onFeedbackChange,
                placeholder = { Text("Describe el motivo (mínimo 10 caracteres)", color = TextMuted) },
                modifier = Modifier.fillMaxWidth(),
                minLines = 4,
                maxLines = 6,
                shape = RoundedCornerShape(10.dp),
                isError = feedbackText.isNotEmpty() && feedbackText.trim().length < 10,
            )

            Text(
                text = "${feedbackText.length} / 500 (mínimo 10)",
                color = if (feedbackText.trim().length in 10..500 || feedbackText.isEmpty()) {
                    TextMuted
                } else {
                    DangerRed
                },
                fontSize = 12.sp,
                modifier = Modifier.align(Alignment.End),
            )

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.End,
            ) {
                TextButton(onClick = onDismiss) {
                    Text("Cancelar", color = TextMuted, fontWeight = FontWeight.Bold)
                }
                Button(
                    onClick = { onConfirm(feedbackText.trim()) },
                    enabled = isValid,
                    shape = RoundedCornerShape(10.dp),
                    colors = ButtonDefaults.buttonColors(containerColor = DangerRed),
                ) {
                    Text("Confirmar rechazo", color = Color.White, fontWeight = FontWeight.ExtraBold)
                }
            }
        }
    }
}
