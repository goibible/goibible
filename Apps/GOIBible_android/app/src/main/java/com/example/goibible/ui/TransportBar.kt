package com.example.goibible.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Slider
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import com.example.goibible.R

/**
 * Movie-style transport for chapters:  |<  <<  [4 ====|---- 40]  >>  >|
 * plus split / lock-sync / settings controls.
 */
@Composable
fun TransportBar(
    chapter: Int,
    chapterCount: Int,
    split: Boolean,
    syncLocked: Boolean,
    onSeek: (Int) -> Unit,
    onFirst: () -> Unit,
    onPrev: () -> Unit,
    onNext: () -> Unit,
    onLast: () -> Unit,
    onToggleSplit: () -> Unit,
    onToggleLock: () -> Unit,
    onSearch: () -> Unit,
    onBookmarks: () -> Unit,
    onRandomizer: () -> Unit,
    onSettings: () -> Unit,
    onAbout: () -> Unit,
) {
    Column(Modifier.fillMaxWidth().padding(horizontal = 8.dp)) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            IconButton(onClick = onFirst) {
                Icon(painterResource(R.drawable.ic_first), contentDescription = "First chapter")
            }
            IconButton(onClick = onPrev) {
                Icon(painterResource(R.drawable.ic_prev), contentDescription = "Previous chapter")
            }
            Text(
                "$chapter",
                modifier = Modifier.width(28.dp),
                textAlign = TextAlign.Center,
                fontWeight = FontWeight.Bold,
                style = MaterialTheme.typography.labelLarge,
            )
            Slider(
                value = chapter.toFloat(),
                onValueChange = { onSeek(it.toInt()) },
                valueRange = 1f..chapterCount.coerceAtLeast(2).toFloat(),
                steps = (chapterCount - 2).coerceAtLeast(0),
                enabled = chapterCount > 1,
                modifier = Modifier.weight(1f),
            )
            Text(
                "$chapterCount",
                modifier = Modifier.width(28.dp),
                textAlign = TextAlign.Center,
                style = MaterialTheme.typography.labelLarge,
            )
            IconButton(onClick = onNext) {
                Icon(painterResource(R.drawable.ic_next), contentDescription = "Next chapter")
            }
            IconButton(onClick = onLast) {
                Icon(painterResource(R.drawable.ic_last), contentDescription = "Last chapter")
            }
        }
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.Center,
            verticalAlignment = Alignment.CenterVertically,
        ) {
            IconButton(onClick = onToggleSplit) {
                Icon(
                    painterResource(R.drawable.ic_split),
                    contentDescription = "Split screen",
                    tint = if (split) MaterialTheme.colorScheme.primary
                    else MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
            if (split) {
                IconButton(onClick = onToggleLock) {
                    Icon(
                        painterResource(if (syncLocked) R.drawable.ic_lock else R.drawable.ic_lock_open),
                        contentDescription = "Lock sync",
                        tint = if (syncLocked) MaterialTheme.colorScheme.primary
                        else MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                }
            }
            IconButton(onClick = onSearch) {
                Icon(
                    painterResource(R.drawable.ic_search),
                    contentDescription = "Search",
                    tint = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
            IconButton(onClick = onBookmarks) {
                Icon(
                    painterResource(R.drawable.ic_bookmark),
                    contentDescription = "Bookmarks",
                    tint = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
            IconButton(onClick = onRandomizer) {
                Icon(
                    painterResource(R.drawable.ic_randomizer),
                    contentDescription = "Random verse",
                    tint = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
            IconButton(onClick = onSettings) {
                Icon(
                    painterResource(R.drawable.ic_settings),
                    contentDescription = "Settings",
                    tint = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
            IconButton(onClick = onAbout) {
                Icon(
                    painterResource(R.drawable.ic_info),
                    contentDescription = "About",
                    tint = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
        }
    }
}
