from pathlib import Path

root = Path("upstream/ARMSX2/platforms/android/app/src/main")
theme_path = root / "java/com/armsx2/ui/theme/Theme.kt"
app_path = root / "java/com/armsx2/ui/settings/AppTab.kt"
theme = theme_path.read_text()
app = app_path.read_text()

old_enum = "enum class ThemeMode { System, MaterialYou, Rgb, Custom, Light, Blue, Purple, Pink, Red, Orange, Green, Teal, Cyan, Black, Oled;"
new_enum = "enum class ThemeMode { System, MaterialYou, Rgb, Custom, Light, Blue, Purple, Pink, Red, Orange, Green, Teal, Cyan, Black, Oled, AnimeDark, AnimeLight, DonghuaDark, DonghuaLight;"
assert old_enum in theme
theme = theme.replace(old_enum, new_enum, 1)

marker = "private val PinkScheme = tintedDark("
assert marker in theme
palettes = """
// EmuCraft character palettes: Anime uses violet/blue; Donghua uses warm gold/bronze.
// Both have dedicated light and dark variants so the character theme never forces a color mode.
private val AnimeDarkScheme = PurpleScheme
private val AnimeLightScheme = DayScheme.copy(
    primary = Color(0xFF6841C8), onPrimary = Color.White,
    primaryContainer = Color(0xFFE9DDFF), onPrimaryContainer = Color(0xFF25104F),
    secondary = Color(0xFF4567B8), onSecondary = Color.White,
    secondaryContainer = Color(0xFFDCE5FF), onSecondaryContainer = Color(0xFF172B5C),
    tertiary = Color(0xFF9A58B5),
)
private val DonghuaDarkScheme = tintedDark(
    accent = Color(0xFFFFC56B), accentContainer = Color(0xFF65451B), onAccentContainer = Color(0xFFFFE7C2),
    background = Color(0xFF171108), surface = Color(0xFF21190D), surfaceRaised = Color(0xFF302313),
    outline = Color(0xFF594326),
)
private val DonghuaLightScheme = DayScheme.copy(
    primary = Color(0xFF966016), onPrimary = Color.White,
    primaryContainer = Color(0xFFFFE8C1), onPrimaryContainer = Color(0xFF321D00),
    secondary = Color(0xFF80552A), onSecondary = Color.White,
    secondaryContainer = Color(0xFFF4DFC4), onSecondaryContainer = Color(0xFF2B1704),
    tertiary = Color(0xFF8B4D38),
)

"""
theme = theme.replace(marker, palettes + marker, 1)
old_when = "        ThemeMode.Oled -> OledScheme\n        ThemeMode.Purple -> PurpleScheme"
new_when = """        ThemeMode.Oled -> OledScheme
        ThemeMode.AnimeDark -> AnimeDarkScheme
        ThemeMode.AnimeLight -> AnimeLightScheme
        ThemeMode.DonghuaDark -> DonghuaDarkScheme
        ThemeMode.DonghuaLight -> DonghuaLightScheme
        ThemeMode.Purple -> PurpleScheme"""
assert old_when in theme
theme = theme.replace(old_when, new_when, 1)

# Persistent EmuCraft-specific presentation preferences.
pref_file = root / "java/com/armsx2/ui/theme/EmuCraftUiPreferences.kt"
pref_file.write_text("""package com.armsx2.ui.theme

import androidx.compose.runtime.mutableStateOf
import androidx.core.content.edit
import com.armsx2.runtime.MainActivityRuntime

/** EmuCraft presentation choices, independent from emulator/core configuration. */
object EmuCraftUiPreferences {
    private const val ModeKey = "emucraft.ui.mode"
    private const val CharacterKey = "emucraft.ui.character"
    private const val MascotKey = "emucraft.ui.mascot"

    val mode = mutableStateOf("Modern")
    val character = mutableStateOf("Anime")
    val mascot = mutableStateOf("Both")

    fun load() {
        mode.value = MainActivityRuntime.prefs.getString(ModeKey, "Modern") ?: "Modern"
        character.value = MainActivityRuntime.prefs.getString(CharacterKey, "Anime") ?: "Anime"
        mascot.value = MainActivityRuntime.prefs.getString(MascotKey, "Both") ?: "Both"
        ToolbarPositionPreferences.set(mode.value == "Console")
        val light = ThemePreferences.mode.value in listOf(ThemeMode.Light, ThemeMode.AnimeLight, ThemeMode.DonghuaLight)
        ThemePreferences.set(
            if (character.value == "Donghua") {
                if (light) ThemeMode.DonghuaLight else ThemeMode.DonghuaDark
            } else {
                if (light) ThemeMode.AnimeLight else ThemeMode.AnimeDark
            }
        )
    }

    fun setMode(value: String) {
        mode.value = value
        MainActivityRuntime.prefs.edit { putString(ModeKey, value) }
        ToolbarPositionPreferences.set(value == "Console")
    }

    fun setCharacter(value: String) {
        character.value = value
        MainActivityRuntime.prefs.edit { putString(CharacterKey, value) }
        val target = when (value) {
            "Donghua" -> if (ThemePreferences.mode.value == ThemeMode.DonghuaLight ||
                ThemePreferences.mode.value == ThemeMode.AnimeLight ||
                ThemePreferences.mode.value == ThemeMode.Light) ThemeMode.DonghuaLight else ThemeMode.DonghuaDark
            else -> if (ThemePreferences.mode.value == ThemeMode.DonghuaLight ||
                ThemePreferences.mode.value == ThemeMode.AnimeLight ||
                ThemePreferences.mode.value == ThemeMode.Light) ThemeMode.AnimeLight else ThemeMode.AnimeDark
        }
        ThemePreferences.set(target)
    }

    fun setMascot(value: String) {
        mascot.value = value
        MainActivityRuntime.prefs.edit { putString(MascotKey, value) }
    }

    fun setColorMode(light: Boolean) {
        ThemePreferences.set(
            if (character.value == "Donghua") {
                if (light) ThemeMode.DonghuaLight else ThemeMode.DonghuaDark
            } else {
                if (light) ThemeMode.AnimeLight else ThemeMode.AnimeDark
            }
        )
    }
}
""")

# Load EmuCraft choices after the upstream theme and toolbar preferences are restored.
runtime_path = root / "java/com/armsx2/runtime/MainActivityRuntime.kt"
runtime = runtime_path.read_text()
load_marker = "        com.armsx2.ui.theme.LibraryChromePreferences.load()"
assert load_marker in runtime
if "EmuCraftUiPreferences.load()" not in runtime:
    runtime = runtime.replace(load_marker, load_marker + "\n        com.armsx2.ui.theme.EmuCraftUiPreferences.load()", 1)
runtime_path.write_text(runtime)

# Add a dedicated EmuCraft appearance panel in the existing App settings.
insert_marker = "        // Library background (wave) color."
assert insert_marker in app
panel = """
        // EmuCraft appearance: two navigation modes, two character art directions,
        // and independent light/dark palettes. These preferences do not touch core settings.
        Column(Modifier.fillMaxWidth().padding(vertical = 8.dp)) {
            Text("EmuCraft Appearance", style = MaterialTheme.typography.titleMedium)
            Text("Choose the interface layout and visual theme.", style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant)
            Spacer(Modifier.height(8.dp))
            Text("Interface mode", style = MaterialTheme.typography.labelLarge)
            FlowRow(horizontalArrangement = Arrangement.spacedBy(7.dp)) {
                listOf("Modern", "Console").forEach { option ->
                    FilterChip(
                        selected = com.armsx2.ui.theme.EmuCraftUiPreferences.mode.value == option,
                        onClick = { com.armsx2.ui.theme.EmuCraftUiPreferences.setMode(option) },
                        label = { Text(option) },
                    )
                }
            }
            Spacer(Modifier.height(8.dp))
            Text("Character theme", style = MaterialTheme.typography.labelLarge)
            FlowRow(horizontalArrangement = Arrangement.spacedBy(7.dp)) {
                listOf("Anime", "Donghua").forEach { option ->
                    FilterChip(
                        selected = com.armsx2.ui.theme.EmuCraftUiPreferences.character.value == option,
                        onClick = { com.armsx2.ui.theme.EmuCraftUiPreferences.setCharacter(option) },
                        label = { Text(option) },
                    )
                }
            }
            Spacer(Modifier.height(8.dp))
            Text("Color mode", style = MaterialTheme.typography.labelLarge)
            FlowRow(horizontalArrangement = Arrangement.spacedBy(7.dp)) {
                val lightSelected = ThemePreferences.mode.value in listOf(
                    ThemeMode.AnimeLight, ThemeMode.DonghuaLight, ThemeMode.Light
                )
                FilterChip(selected = !lightSelected,
                    onClick = { com.armsx2.ui.theme.EmuCraftUiPreferences.setColorMode(false) },
                    label = { Text("Dark") })
                FilterChip(selected = lightSelected,
                    onClick = { com.armsx2.ui.theme.EmuCraftUiPreferences.setColorMode(true) },
                    label = { Text("Light") })
            }
            Spacer(Modifier.height(8.dp))
            Text("Chibi mascot", style = MaterialTheme.typography.labelLarge)
            FlowRow(horizontalArrangement = Arrangement.spacedBy(7.dp)) {
                listOf("Anime", "Donghua", "Both").forEach { option ->
                    FilterChip(
                        selected = com.armsx2.ui.theme.EmuCraftUiPreferences.mascot.value == option,
                        onClick = { com.armsx2.ui.theme.EmuCraftUiPreferences.setMascot(option) },
                        label = { Text(option) },
                    )
                }
            }
        }

"""
app = app.replace(insert_marker, panel + insert_marker, 1)

# Keep EmuCraft-specific theme presets in the dedicated appearance panel instead of
# duplicating them in the upstream generic color-theme picker.
app = app.replace(
    "ThemeMode.entries.filter {",
    "ThemeMode.entries.filter { it !in listOf(ThemeMode.AnimeDark, ThemeMode.AnimeLight, ThemeMode.DonghuaDark, ThemeMode.DonghuaLight) }.filter {",
    1,
)

# Animated, touch-reactive vector chibi mascot. It is drawn in Compose so it needs no
# downloaded artwork, does not bundle third-party character IP, and stays lightweight.
mascot_path = root / "java/com/armsx2/ui/home/EmuCraftMascot.kt"
mascot_path.write_text("""package com.armsx2.ui.home

import androidx.compose.animation.core.LinearEasing
import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.shadow
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.unit.dp
import com.armsx2.ui.theme.EmuCraftUiPreferences

@Composable
fun EmuCraftMascotOverlay() {
    if (EmuCraftUiPreferences.mascot.value == "Off") return
    var donghua by remember { mutableStateOf(EmuCraftUiPreferences.character.value == "Donghua") }
    val motion = rememberInfiniteTransition(label = "emucraftMascot")
    val bob by motion.animateFloat(-2.5f, 2.5f,
        infiniteRepeatable(tween(1900, easing = LinearEasing), RepeatMode.Reverse), label = "float")
    val breeze by motion.animateFloat(-1f, 1f,
        infiniteRepeatable(tween(2300, easing = LinearEasing), RepeatMode.Reverse), label = "breeze")
    val wave by motion.animateFloat(-0.18f, 0.42f,
        infiniteRepeatable(tween(720, easing = LinearEasing), RepeatMode.Reverse), label = "wave")
    val glow by motion.animateFloat(-0.8f, 0.8f,
        infiniteRepeatable(tween(2600, easing = LinearEasing), RepeatMode.Restart), label = "glow")
    val blink by motion.animateFloat(1f, 0.08f,
        infiniteRepeatable(tween(110, delayMillis = 3100), RepeatMode.Reverse), label = "blink")
    val accent = if (donghua) Color(0xFFFFC56B) else Color(0xFFB58AFF)
    val hair = if (donghua) Color(0xFF38251A) else Color(0xFF29213D)
    val robe = if (donghua) Color(0xFF80552A) else Color(0xFF51408D)

    Box(Modifier.padding(10.dp), contentAlignment = Alignment.Center) {
        Canvas(Modifier.size(82.dp).shadow(7.dp, CircleShape).clickable { donghua = !donghua }) {
            val w = size.width
            val h = size.height
            val cx = w * 0.49f
            val cy = h * 0.39f + bob
            val head = w * 0.235f
            val halo = Offset(cx, cy + head * 0.2f)

            // Soft aura and a travelling highlight give the badge a restrained premium glow.
            drawCircle(Brush.radialGradient(listOf(accent.copy(alpha = 0.25f), Color.Transparent),
                center = halo, radius = w * 0.49f), radius = w * 0.49f, center = halo)
            val sweepX = w * (0.18f + (glow + 0.8f) * 0.40f)
            drawLine(accent.copy(alpha = 0.30f), Offset(sweepX, h * 0.12f),
                Offset(sweepX + w * 0.22f, h * 0.78f), strokeWidth = w * 0.045f)

            // Wind-swept back hair / ribbon.
            val backHair = Path().apply {
                moveTo(cx - head * 0.65f, cy - head * 0.30f)
                cubicTo(cx - head * 1.8f, cy - head * 1.05f + breeze * 3f,
                    cx - head * 1.8f, cy + head * 0.25f + breeze * 5f,
                    cx - head * 1.25f, cy + head * 0.55f + breeze * 3f)
                cubicTo(cx - head * 0.8f, cy + head * 0.15f, cx - head * 0.5f, cy, cx - head * 0.65f, cy - head * 0.30f)
                close()
            }
            drawPath(backHair, hair)

            // Small robe silhouette and scarf tails that sway with the breeze.
            val robePath = Path().apply {
                moveTo(cx - head * 0.78f, cy + head * 0.92f)
                quadraticTo(cx, cy + head * 0.55f, cx + head * 0.78f, cy + head * 0.92f)
                lineTo(cx + head * 1.10f, cy + head * 2.35f)
                quadraticTo(cx, cy + head * 2.72f, cx - head * 1.10f, cy + head * 2.35f)
                close()
            }
            drawPath(robePath, robe)
            val scarf = Path().apply {
                moveTo(cx + head * 0.45f, cy + head * 0.90f)
                cubicTo(cx + head * 1.25f, cy + head * 1.25f + breeze * 5f,
                    cx + head * 1.65f, cy + head * 1.00f + breeze * 8f,
                    cx + head * 1.85f, cy + head * 1.40f + breeze * 7f)
                lineTo(cx + head * 1.38f, cy + head * 1.65f + breeze * 6f)
                quadraticTo(cx + head * 0.95f, cy + head * 1.35f, cx + head * 0.45f, cy + head * 0.90f)
                close()
            }
            drawPath(scarf, accent.copy(alpha = 0.88f))

            // Raised waving arm, animated gently at the wrist.
            val shoulder = Offset(cx + head * 0.70f, cy + head * 1.20f)
            val elbow = Offset(cx + head * 1.28f, cy + head * 0.85f)
            val hand = Offset(cx + head * (1.42f + wave * 0.28f), cy + head * (0.30f + wave * 0.10f))
            drawLine(robe.copy(alpha = 0.95f), shoulder, elbow, strokeWidth = head * 0.30f)
            drawLine(Color(0xFFFFDCCB), elbow, hand, strokeWidth = head * 0.22f)
            drawCircle(Color(0xFFFFDCCB), head * 0.16f, hand)

            // Face, hair cap and a clean highlight on the fringe.
            drawCircle(hair, head * 1.12f, Offset(cx, cy - head * 0.06f))
            drawCircle(Color(0xFFFFDCCB), head * 0.88f, Offset(cx, cy + head * 0.16f))
            val fringe = Path().apply {
                moveTo(cx - head * 0.92f, cy - head * 0.08f)
                cubicTo(cx - head * 0.70f, cy - head * 1.45f, cx + head * 0.05f, cy - head * 1.20f, cx + head * 0.18f, cy - head * 0.48f)
                cubicTo(cx + head * 0.55f, cy - head * 1.00f, cx + head * 0.95f, cy - head * 0.58f, cx + head * 0.90f, cy + head * 0.02f)
                close()
            }
            drawPath(fringe, hair)
            drawLine(accent.copy(alpha = 0.8f), Offset(cx - head * 0.45f, cy - head * 0.67f),
                Offset(cx + head * 0.12f, cy - head * 0.82f), strokeWidth = head * 0.075f)

            val eyeY = cy + head * 0.20f
            drawLine(Color(0xFF38283C), Offset(cx - head * 0.48f, eyeY),
                Offset(cx - head * 0.20f, eyeY), strokeWidth = head * 0.10f, alpha = blink)
            drawLine(Color(0xFF38283C), Offset(cx + head * 0.20f, eyeY),
                Offset(cx + head * 0.48f, eyeY), strokeWidth = head * 0.10f, alpha = blink)
            drawCircle(Color(0xFFE99A9A), head * 0.075f, Offset(cx - head * 0.53f, cy + head * 0.43f), alpha = 0.55f)
            drawCircle(Color(0xFFE99A9A), head * 0.075f, Offset(cx + head * 0.53f, cy + head * 0.43f), alpha = 0.55f)

            // Fine orbit ring and two moving light particles.
            drawCircle(accent.copy(alpha = 0.68f), w * 0.43f, Offset(cx, cy + head * 0.55f),
                style = Stroke(width = 1.15.dp.toPx()))
            drawCircle(Color.White.copy(alpha = 0.72f), w * 0.025f,
                Offset(w * (0.24f + (glow + 0.8f) * 0.25f), h * 0.25f))
            drawCircle(accent.copy(alpha = 0.85f), w * 0.018f,
                Offset(w * (0.78f - (glow + 0.8f) * 0.18f), h * 0.70f))
        }
    }
}
""")

# Overlay the mascot on the game library without intercepting the rest of the screen.
home_path = root / "java/com/armsx2/ui/home/HomeScreen.kt"
home = home_path.read_text()
home_marker = "            val compact = maxWidth < 600.dp"
assert home_marker in home
if "EmuCraftMascotOverlay()" not in home:
    home = home.replace(home_marker, home_marker + "\n            Box(Modifier.align(Alignment.BottomEnd)) { EmuCraftMascotOverlay() }", 1)
home_path.write_text(home)

theme_path.write_text(theme)
app_path.write_text(app)
print("Applied EmuCraft theme palettes and appearance controls.")
