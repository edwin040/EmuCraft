from pathlib import Path
import math
import struct
import wave

root = Path("upstream/ARMSX2/platforms/android/app/src/main")

# Optional user-provided Donghua artwork is stored in the repository at assets/donghua-bg.webp.
# Copy it into Android drawable resources when present; the build remains valid without it.
asset_source = Path("assets/donghua-bg.webp")
if asset_source.exists():
    asset_target = Path("upstream/ARMSX2/platforms/android/app/src/main/res/drawable-nodpi/emucraft_donghua_bg.webp")
    asset_target.parent.mkdir(parents=True, exist_ok=True)
    asset_target.write_bytes(asset_source.read_bytes())


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
    private const val AmbientKey = "emucraft.ui.ambient"

    val mode = mutableStateOf("Modern")
    val character = mutableStateOf("Anime")
    val ambientEnabled = mutableStateOf(false)

    fun load() {
        mode.value = MainActivityRuntime.prefs.getString(ModeKey, "Modern") ?: "Modern"
        character.value = MainActivityRuntime.prefs.getString(CharacterKey, "Anime") ?: "Anime"
        ambientEnabled.value = MainActivityRuntime.prefs.getBoolean(AmbientKey, false)
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

    fun setAmbientEnabled(value: Boolean) {
        ambientEnabled.value = value
        MainActivityRuntime.prefs.edit { putBoolean(AmbientKey, value) }
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
            Text("Ambient soundtrack", style = MaterialTheme.typography.labelLarge)
            FilterChip(
                selected = com.armsx2.ui.theme.EmuCraftUiPreferences.ambientEnabled.value,
                onClick = { com.armsx2.ui.theme.EmuCraftUiPreferences.setAmbientEnabled(!com.armsx2.ui.theme.EmuCraftUiPreferences.ambientEnabled.value) },
                label = { Text(if (com.armsx2.ui.theme.EmuCraftUiPreferences.ambientEnabled.value) "Sound On" else "Sound Off") },
            )
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


# Animated Anime/Donghua atmosphere: full-screen color field, moving curved light ribbons,
# drifting spark fragments, and restrained glow. The native backdrop remains underneath.
visual_path = root / "java/com/armsx2/ui/home/EmuCraftAnimatedBackground.kt"
visual_path.write_text("""package com.armsx2.ui.home

import androidx.compose.animation.core.LinearEasing
import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.ImageBitmap
import androidx.compose.ui.res.imageResource
import androidx.compose.ui.unit.IntSize
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.unit.dp
import com.armsx2.ui.theme.EmuCraftUiPreferences
import com.armsx2.ui.theme.ThemeMode
import com.armsx2.ui.theme.ThemePreferences
import kotlin.math.PI
import kotlin.math.sin

@Composable
fun EmuCraftAnimatedBackground(modifier: Modifier = Modifier) {
    val donghua = EmuCraftUiPreferences.character.value == "Donghua"
    val light = ThemePreferences.mode.value in listOf(ThemeMode.AnimeLight, ThemeMode.DonghuaLight)
    val deep = if (donghua) Color(0xFF21170E) else Color(0xFF15132A)
    val mid = if (donghua) Color(0xFF573A20) else Color(0xFF30245C)
    val accent = if (donghua) Color(0xFFFFC66E) else Color(0xFF9C83FF)
    val secondary = if (donghua) Color(0xFFE99A45) else Color(0xFF4CA7FF)
    val transition = rememberInfiniteTransition(label = "emucraftAtmosphere")
    val drift by transition.animateFloat(0f, 1f,
        infiniteRepeatable(tween(18000, easing = LinearEasing), RepeatMode.Restart), label = "drift")
    val shimmer by transition.animateFloat(0f, 1f,
        infiniteRepeatable(tween(7200, easing = LinearEasing), RepeatMode.Restart), label = "shimmer")

    Canvas(modifier.fillMaxSize()) {
        val w = size.width
        val h = size.height
        val base = if (light) {
            if (donghua) Color(0xFFB58A57) else Color(0xFF6678A8)
        } else deep
        val upper = if (light) {
            if (donghua) Color(0xFF6F5033) else Color(0xFF343C70)
        } else mid
        drawRect(Brush.verticalGradient(listOf(upper.copy(alpha = if (donghuaArtwork != null) 0.10f else 0.88f), base.copy(alpha = if (donghuaArtwork != null) 0.14f else 0.94f), deep.copy(alpha = if (donghuaArtwork != null) 0.20f else 0.98f))))

        // Broad atmospheric glow, deliberately low contrast behind game covers and labels.
        drawCircle(
            Brush.radialGradient(listOf(accent.copy(alpha = if (light) 0.12f else 0.19f), Color.Transparent),
                center = Offset(w * (0.22f + drift * 0.56f), h * 0.34f), radius = w * 0.72f),
            radius = w * 0.72f, center = Offset(w * (0.22f + drift * 0.56f), h * 0.34f)
        )

        // Two elegant curved ribbons, travelling slowly across the scene.
        for (i in 0..2) {
            val phase = (drift + i * 0.31f) % 1f
            val path = Path().apply {
                moveTo(-w * 0.12f, h * (0.30f + i * 0.16f))
                cubicTo(w * (0.18f + phase * 0.22f), h * (0.02f + i * 0.12f),
                    w * (0.58f - phase * 0.12f), h * (0.82f - i * 0.10f),
                    w * 1.12f, h * (0.38f + i * 0.14f))
            }
            drawPath(path, accent.copy(alpha = (if (light) 0.15f else 0.27f) - i * 0.045f),
                style = Stroke(width = (2.4f - i * 0.45f).dp.toPx()))
            drawPath(path, Brush.linearGradient(listOf(Color.Transparent, secondary.copy(alpha = 0.26f), Color.Transparent)),
                style = Stroke(width = (8f - i).dp.toPx()))
        }

        // Dimensional rift fragments: angular glass-like shards drift and rotate gently.
        for (i in 0 until 18) {
            val seed = i * 0.6180339f
            val x = ((seed + drift * (0.035f + (i % 4) * 0.018f)) % 1f) * w
            val y = (((i * 0.217f) + drift * (if (i % 2 == 0) 0.075f else -0.055f) + 1f) % 1f) * h
            val pulse = 0.35f + 0.65f * ((sin(shimmer * 2f * PI.toFloat() + i * 1.7f) + 1f) / 2f)
            val shardW = (5f + (i % 4) * 2.5f) * density
            val shardH = (13f + (i % 5) * 4f) * density
            val tilt = sin(drift * 2f * PI.toFloat() + i) * shardW * 0.7f
            val shard = Path().apply {
                moveTo(x, y - shardH)
                lineTo(x + shardW + tilt, y - shardH * 0.12f)
                lineTo(x + tilt * 0.25f, y + shardH)
                lineTo(x - shardW * 0.55f, y + shardH * 0.18f)
                close()
            }
            drawPath(shard, secondary.copy(alpha = pulse * 0.20f))
            drawPath(shard, accent.copy(alpha = pulse * 0.56f), style = Stroke(width = 0.8f.dp.toPx()))
        }

        // Fine light particles and occasional bright glints; no flowers or petal shapes.
        for (i in 0 until 42) {
            val seed = i * 0.75487766f
            val x = ((seed + drift * (0.055f + (i % 6) * 0.014f)) % 1f) * w
            val y = (((i * 0.137f) + drift * (if (i % 2 == 0) 0.11f else -0.08f) + 1f) % 1f) * h
            val pulse = (sin(shimmer * 2f * PI.toFloat() + i * 1.31f) + 1f) / 2f
            val radius = (0.9f + (i % 3) * 0.55f) * density
            drawCircle(if (i % 4 == 0) secondary.copy(alpha = 0.24f + pulse * 0.42f)
                else accent.copy(alpha = 0.18f + pulse * 0.48f), radius, Offset(x, y))
        }


    }
}
""")

audio_path = root / "java/com/armsx2/ui/home/EmuCraftAmbientAudio.kt"
audio_path.write_text("""package com.armsx2.ui.home

import android.content.Context
import android.media.MediaPlayer
import com.armsx2.R

/** Original, locally bundled ambient loop. No network, ads, or third-party music service. */
object EmuCraftAmbientAudio {
    private var player: MediaPlayer? = null

    @Synchronized fun start(context: Context) {
        if (player?.isPlaying == true) return
        stop()
        player = MediaPlayer.create(context.applicationContext, R.raw.emucraft_ambient)?.apply {
            isLooping = true
            setVolume(0.22f, 0.22f)
            start()
        }
    }

    @Synchronized fun stop() {
        runCatching { player?.stop() }
        runCatching { player?.release() }
        player = null
    }
}
""")

# Generate a gentle original ambient pad loop at build time (no copyrighted soundtrack).
raw_dir = root / "res/raw"
raw_dir.mkdir(parents=True, exist_ok=True)
wav_path = raw_dir / "emucraft_ambient.wav"
sample_rate = 22050
duration = 16
notes = [(130.81, 164.81, 196.00), (110.00, 146.83, 174.61),
         (123.47, 155.56, 185.00), (98.00, 130.81, 164.81)]
with wave.open(str(wav_path), "wb") as wav:
    wav.setnchannels(1)
    wav.setsampwidth(2)
    wav.setframerate(sample_rate)
    frames = bytearray()
    total = sample_rate * duration
    for n in range(total):
        t = n / sample_rate
        chord = notes[int(t // 4) % len(notes)]
        fade = min(1.0, t / 1.5, (duration - t) / 1.5)
        pad = sum(math.sin(2 * math.pi * f * t) * (0.55 if j == 0 else 0.28 if j == 1 else 0.18)
                  for j, f in enumerate(chord))
        shimmer_t = t % 4.0
        bell_freq = chord[1] * (2.0 if shimmer_t < 2.0 else 2.5)
        bell = math.sin(2 * math.pi * bell_freq * t) * math.exp(-((shimmer_t - 0.4) % 2.0) * 2.8) * 0.10
        sample = max(-1.0, min(1.0, (pad * 0.055 + bell) * fade))
        frames.extend(struct.pack("<h", int(sample * 32767)))
    wav.writeframes(frames)

# The sound follows the user's explicit toggle and is stopped when the library screen leaves.
home_path = root / "java/com/armsx2/ui/home/HomeScreen.kt"
home = home_path.read_text()
audio_anchor = '    val context = LocalContext.current\n'
if audio_anchor not in home:
    raise RuntimeError("HomeScreen context anchor missing for ambient audio host")
home = home.replace(audio_anchor, audio_anchor + """    DisposableEffect(com.armsx2.ui.theme.EmuCraftUiPreferences.ambientEnabled.value) {
        if (com.armsx2.ui.theme.EmuCraftUiPreferences.ambientEnabled.value) {
            EmuCraftAmbientAudio.start(context)
        } else {
            EmuCraftAmbientAudio.stop()
        }
        onDispose { EmuCraftAmbientAudio.stop() }
    }
""", 1)

# Add the animated visual layer after the readability scrim, still below library controls.
visual_anchor = """                )
            }
        },
    ) {
"""
if visual_anchor not in home:
    raise RuntimeError("HomeScreen background-layer insertion anchor missing")
home = home.replace(visual_anchor, """                )
                EmuCraftAnimatedBackground(Modifier.fillMaxSize())
            }
        },
    ) {
""", 1)
home_path.write_text(home)

# Mascot artwork and overlay are intentionally omitted from EmuCraft UI.

# No floating mascot overlay: keep the game library focused on emulator controls.

theme_path.write_text(theme)
app_path.write_text(app)

# Connect EmuCraft performance profiles to the actual PCSX2 Settings model.
# The upstream Settings.applyTo() writes these values through NativeApp.setSetting()
# and ConfigStore/InGameOverlay persist them globally or per game.
profiles_path = root / "java/com/armsx2/config/EmuCraftPerformanceProfiles.kt"
profiles_path.write_text("""package com.armsx2.config

import android.content.Context
import com.armsx2.DeviceTier

/** Presets modify the real PCSX2 Settings model; Settings.applyTo() commits them to emucore. */
object EmuCraftPerformanceProfiles {
    const val FPS_MAX = 0
    const val GRAPHICS_MAX = 1
    const val DEVICE_PERFORMANCE = 2
    const val MANUAL = 3

    fun apply(profile: Int, base: Settings, context: Context): Settings = when (profile) {
        FPS_MAX -> base.copy(
            cpu = base.cpu.copy(
                eeCycleRate = 0, eeCycleSkip = 1,
                mtvu = DeviceTier.mtvuDefault(), fastCDVD = true,
                vu1Instant = true, vuFlagHack = true, intcStat = true, waitLoop = true,
            ),
            output = base.output.copy(upscaleFloat = 1.0f),
            graphics = base.graphics.copy(
                accurateBlendingUnit = 0, hwMipmap = false, texturePreloading = 1,
            ),
            display = base.display.copy(hwRov = false),
        )
        GRAPHICS_MAX -> base.copy(
            cpu = base.cpu.copy(eeCycleRate = 0, eeCycleSkip = 0, fastCDVD = false),
            output = base.output.copy(upscaleFloat = 2.0f),
            graphics = base.graphics.copy(
                accurateBlendingUnit = 2, hwMipmap = true, texturePreloading = 2,
                fxaa = true,
            ),
        )
        DEVICE_PERFORMANCE -> if (DeviceTier.isLowEnd(context)) {
            Settings.lowEndPreset(base, DeviceTier.mtvuDefault())
        } else {
            base.copy(
                cpu = base.cpu.copy(eeCycleRate = 0, eeCycleSkip = 0, mtvu = DeviceTier.mtvuDefault()),
                output = base.output.copy(upscaleFloat = 1.5f),
                graphics = base.graphics.copy(
                    accurateBlendingUnit = 1, hwMipmap = true, texturePreloading = 2,
                ),
            )
        }
        else -> base // Manual is intentionally non-destructive.
    }

    /** Detect only exact, known presets. Any user-tuned combination is Manual. */
    fun detect(settings: Settings, context: Context): Int {
        if (matches(settings, FPS_MAX, context)) return FPS_MAX
        if (matches(settings, GRAPHICS_MAX, context)) return GRAPHICS_MAX
        if (matches(settings, DEVICE_PERFORMANCE, context)) return DEVICE_PERFORMANCE
        return MANUAL
    }

    private fun matches(settings: Settings, profile: Int, context: Context): Boolean {
        val expected = apply(profile, Settings(), context)
        return settings.cpu.eeCycleRate == expected.cpu.eeCycleRate &&
            settings.cpu.eeCycleSkip == expected.cpu.eeCycleSkip &&
            settings.cpu.mtvu == expected.cpu.mtvu &&
            settings.cpu.fastCDVD == expected.cpu.fastCDVD &&
            settings.output.upscaleFloat == expected.output.upscaleFloat &&
            settings.graphics.accurateBlendingUnit == expected.graphics.accurateBlendingUnit &&
            settings.graphics.hwMipmap == expected.graphics.hwMipmap &&
            settings.graphics.texturePreloading == expected.graphics.texturePreloading &&
            (profile != GRAPHICS_MAX || settings.graphics.fxaa == expected.graphics.fxaa)
    }
}
""")

performance_path = root / "java/com/armsx2/ui/settings/PerformanceTab.kt"
performance = performance_path.read_text()
profile_marker = "        // Speedhack profile presets. Equality against s.copy(...) means the"
assert profile_marker in performance
profile_ui = """
        // EmuCraft profiles write real CPU/GS settings through the same scoped save path.
        run {
            val context = androidx.compose.ui.platform.LocalContext.current
            val selected = com.armsx2.config.EmuCraftPerformanceProfiles.detect(s, context)
            SegmentedRow(
                label = "EmuCraft performance profile",
                options = listOf("FPS Max", "Graphics Max", "Device Performance", "Normal / Manual"),
                selectedIndex = selected,
                description = "Changes supported PCSX2 CPU and graphics settings. Manual keeps your current values.",
                onChange = { profile ->
                    if (profile != com.armsx2.config.EmuCraftPerformanceProfiles.MANUAL) {
                        apply(com.armsx2.config.EmuCraftPerformanceProfiles.apply(profile, s, context))
                    }
                },
                field = "emucraftPerformanceProfile",
            )
        }
        HelpText("Profiles are applied to the active Global/Game settings scope. Manual does not overwrite custom values.")
        SettingsDivider()
"""
performance = performance.replace(profile_marker, profile_ui + profile_marker, 1)
performance_path.write_text(performance)

print("Applied EmuCraft animated Anime/Donghua backgrounds, performance profiles, optional ambient soundtrack, and removed mascot overlay.")
