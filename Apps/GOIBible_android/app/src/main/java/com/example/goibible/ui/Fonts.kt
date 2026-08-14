@file:OptIn(ExperimentalTextApi::class)

package com.example.goibible.ui

import androidx.compose.ui.text.ExperimentalTextApi
import androidx.compose.ui.text.font.Font
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontVariation
import androidx.compose.ui.text.font.FontWeight
import com.example.goibible.R

private val Literata = FontFamily(
    Font(
        R.font.literata,
        weight = FontWeight.Normal,
        variationSettings = FontVariation.Settings(FontVariation.weight(400)),
    ),
    Font(
        R.font.literata,
        weight = FontWeight.Bold,
        variationSettings = FontVariation.Settings(FontVariation.weight(700)),
    ),
)

/** Reader font choices offered in Settings; key is what gets persisted. */
val FontChoices = listOf(
    "literata" to "Literata",
    "serif" to "Serif",
    "sans" to "Sans",
    "mono" to "Mono",
)

fun readerFontFamily(key: String): FontFamily = when (key) {
    "literata" -> Literata
    "serif" -> FontFamily.Serif
    "mono" -> FontFamily.Monospace
    else -> FontFamily.SansSerif
}
