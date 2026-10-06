package com.marketmind.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/** Cuenta donde se publicará (o se publicó) la campaña al aprobarla. */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class DestinoDTO {
    private String red;
    private String cuentaNombre;
    private String estado;
    private String permalink;
}
