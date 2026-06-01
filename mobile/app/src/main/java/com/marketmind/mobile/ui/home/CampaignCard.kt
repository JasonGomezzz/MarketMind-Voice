package com.marketmind.mobile.ui.home

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.AssistChip
import androidx.compose.material3.AssistChipDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.marketmind.mobile.data.remote.dto.CampaignDto

@Composable
fun CampaignCard(
    campaign: CampaignDto,
    onClick: (Long) -> Unit,
    modifier: Modifier = Modifier,
) {
    Card(
        onClick = { onClick(campaign.id) },
        modifier = modifier.fillMaxWidth(),
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
                    style = MaterialTheme.typography.titleMedium,
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
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }

            val extracto = campaign.textoGenerado?.takeIf { it.isNotBlank() }
                ?: campaign.prompt
            extracto?.takeIf { it.isNotBlank() }?.let {
                Text(
                    text = it.trim().take(120).let { snippet ->
                        if (it.length > 120) "$snippet…" else snippet
                    },
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }

            campaign.fechaCreacion?.let { iso ->
                Text(
                    text = formatFecha(iso),
                    style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.outline,
                )
            }
        }
    }
}

private fun formatEstado(raw: String): String =
    raw.replace('_', ' ').replaceFirstChar { it.uppercase() }

private fun formatFecha(iso: String): String =
    iso.take(10).let { date ->
        runCatching {
            val (y, m, d) = date.split("-")
            "$d/$m/$y"
        }.getOrDefault(date)
    }
