package com.emucraft

import android.app.Activity
import android.content.Intent
import android.database.Cursor
import android.graphics.Color
import android.net.Uri
import android.os.Bundle
import android.provider.OpenableColumns
import android.view.View
import android.widget.Button
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import java.io.File
import java.util.Locale
import java.util.concurrent.Executors

class MainActivity : Activity() {
    private lateinit var gameLabel: TextView
    private lateinit var biosLabel: TextView
    private lateinit var engineStatus: TextView
    private var gameUri: Uri? = null
    private var biosUri: Uri? = null
    private var gameFile: File? = null
    private var biosFile: File? = null
    private val importExecutor = Executors.newSingleThreadExecutor()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        window.statusBarColor = BG
        window.navigationBarColor = BG

        val prefs = getSharedPreferences(PREFS, MODE_PRIVATE)
        gameUri = prefs.getString(KEY_GAME_URI, null)?.let(Uri::parse)
        biosUri = prefs.getString(KEY_BIOS_URI, null)?.let(Uri::parse)
        gameFile = prefs.getString(KEY_GAME_PATH, null)?.let(::File)?.takeIf { it.isFile && it.length() > 0L }
        biosFile = prefs.getString(KEY_BIOS_PATH, null)?.let(::File)?.takeIf { it.isFile && it.length() > 0L }

        val content = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(22), dp(26), dp(22), dp(28))
            setBackgroundColor(BG)
        }
        content.addView(label("EMUCRAFT", 13, ACCENT, true))
        content.addView(label("PS2 Emulator", 30, Color.WHITE, true).apply {
            setPadding(0, dp(7), 0, dp(3))
        })
        content.addView(label("Android • ARM64 • Performance-first", 13, MUTED, false))
        content.addView(space(22))

        val statusPanel = panel()
        statusPanel.addView(label("ENGINE STATUS", 11, ACCENT, true))
        engineStatus = label(nativeStatus(), 14, Color.WHITE, false).apply {
            setPadding(0, dp(10), 0, 0)
        }
        statusPanel.addView(engineStatus)
        content.addView(statusPanel)
        content.addView(space(22))

        content.addView(label("GAME LIBRARY", 12, MUTED, true))
        gameLabel = label("No PS2 game selected", 14, Color.WHITE, false).apply {
            setPadding(0, dp(12), 0, dp(10))
        }
        content.addView(gameLabel)
        content.addView(actionButton("Add PS2 game file") { chooseFile(REQUEST_GAME) })
        content.addView(space(20))

        content.addView(label("BIOS CONFIGURATION", 12, MUTED, true))
        biosLabel = label("No BIOS selected", 14, Color.WHITE, false).apply {
            setPadding(0, dp(12), 0, dp(10))
        }
        content.addView(biosLabel)
        content.addView(actionButton("Select PS2 BIOS") { chooseFile(REQUEST_BIOS) })
        content.addView(space(20))

        val note = panel()
        note.addView(label("IMPORTANT", 11, 0xFFFFC56B.toInt(), true))
        note.addView(label(
            "Selected files are copied into EmuCraft's private storage so the future native core can read normal file paths. This does not yet validate or run games.",
            13, Color.WHITE, false
        ).apply { setPadding(0, dp(8), 0, 0) })
        content.addView(note)
        content.addView(space(22))

        content.addView(label("DEVELOPMENT ROADMAP", 12, MUTED, true))
        listOf(
            "✓ Android ARM64 build foundation",
            "✓ Native C++ bridge and SAF file selection",
            "✓ Private game / BIOS staging with SHA-256",
            "→ Integrate and compile PS2 core",
            "→ Renderer, audio and controller pipeline",
            "→ Compatibility and performance testing"
        ).forEach {
            content.addView(label(it, 14, Color.WHITE, false).apply {
                setPadding(0, dp(8), 0, dp(8))
            })
        }

        val scroll = ScrollView(this).apply { addView(content) }
        setContentView(scroll)
        refreshFileLabels()
    }

    private fun nativeStatus(): String = try {
        NativeBridge.engineStatus()
    } catch (error: UnsatisfiedLinkError) {
        "Native engine library could not be loaded: ${error.message ?: "unknown error"}"
    } catch (error: Exception) {
        "Native status unavailable: ${error.message ?: "unknown error"}"
    }

    private fun chooseFile(requestCode: Int) {
        val intent = Intent(Intent.ACTION_OPEN_DOCUMENT).apply {
            addCategory(Intent.CATEGORY_OPENABLE)
            type = "*/*"
            addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION or Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION)
        }
        startActivityForResult(intent, requestCode)
    }

    @Deprecated("Uses Android Storage Access Framework to retain access to user-selected files.")
    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (resultCode != RESULT_OK) return
        val uri = data?.data ?: return
        if (requestCode != REQUEST_GAME && requestCode != REQUEST_BIOS) return

        val name = queryDisplayName(uri)
        val extension = name.substringAfterLast('.', "").lowercase(Locale.ROOT)
        val accepted = if (requestCode == REQUEST_GAME) {
            extension in GAME_EXTENSIONS
        } else {
            extension in BIOS_EXTENSIONS
        }
        if (!accepted) {
            engineStatus.text = if (requestCode == REQUEST_GAME) {
                "Unsupported game-file extension. Choose ISO, CHD, CSO or BIN."
            } else {
                "Unsupported BIOS-file extension. Choose BIN, ROM or BIOS."
            }
            return
        }

        try {
            val readFlag = data.flags and Intent.FLAG_GRANT_READ_URI_PERMISSION
            if (readFlag != 0) contentResolver.takePersistableUriPermission(uri, readFlag)
        } catch (_: SecurityException) {
            // Import immediately below while the temporary SAF grant is still active.
        }

        val isGame = requestCode == REQUEST_GAME
        if (isGame) gameUri = uri else biosUri = uri
        val prefs = getSharedPreferences(PREFS, MODE_PRIVATE)
        prefs.edit()
            .putString(if (isGame) KEY_GAME_URI else KEY_BIOS_URI, uri.toString())
            .apply()

        engineStatus.text = "Importing $name into private app storage…"
        refreshFileLabels()

        importExecutor.execute {
            try {
                val imported = GameFileImporter.import(
                    resolver = contentResolver,
                    uri = uri,
                    displayName = name,
                    kind = if (isGame) "game" else "bios",
                    filesDirectory = filesDir
                )
                runOnUiThread {
                    if (isGame) gameFile = imported.file else biosFile = imported.file
                    prefs.edit()
                        .putString(if (isGame) KEY_GAME_PATH else KEY_BIOS_PATH, imported.file.absolutePath)
                        .apply()
                    refreshFileLabels()
                    engineStatus.text = buildString {
                        append(if (isGame) "Game file imported successfully." else "BIOS file imported successfully.")
                        append(" SHA-256: ")
                        append(imported.sha256)
                        append(". PS2 core is not connected yet.")
                    }
                }
            } catch (error: Exception) {
                runOnUiThread {
                    engineStatus.text = "File import failed: ${error.message ?: error.javaClass.simpleName}"
                    refreshFileLabels()
                }
            }
        }
    }

    private fun refreshFileLabels() {
        gameLabel.text = describeFile(gameFile, gameUri, "No PS2 game selected")
        biosLabel.text = describeFile(biosFile, biosUri, "No BIOS selected")
    }

    private fun describeFile(file: File?, uri: Uri?, emptyText: String): String {
        if (file != null && file.isFile && file.length() > 0L) {
            return "Ready: ${file.name}\n${formatSize(file.length())} • Private app storage"
        }
        return uri?.let { "Selected: ${queryDisplayName(it)} (not imported)" } ?: emptyText
    }

    private fun formatSize(bytes: Long): String {
        if (bytes < 1024L) return "$bytes B"
        val units = arrayOf("KB", "MB", "GB", "TB")
        var value = bytes.toDouble()
        var unit = -1
        do {
            value /= 1024.0
            unit++
        } while (value >= 1024.0 && unit < units.lastIndex)
        return String.format(Locale.ROOT, "%.2f %s", value, units[unit])
    }

    private fun queryDisplayName(uri: Uri): String {
        var cursor: Cursor? = null
        return try {
            cursor = contentResolver.query(uri, arrayOf(OpenableColumns.DISPLAY_NAME), null, null, null)
            if (cursor != null && cursor.moveToFirst()) {
                cursor.getString(cursor.getColumnIndexOrThrow(OpenableColumns.DISPLAY_NAME)) ?: "Selected file"
            } else uri.lastPathSegment ?: "Selected file"
        } catch (_: Exception) {
            uri.lastPathSegment ?: "Selected file"
        } finally {
            cursor?.close()
        }
    }

    override fun onDestroy() {
        importExecutor.shutdown()
        super.onDestroy()
    }

    private fun panel() = LinearLayout(this).apply {
        orientation = LinearLayout.VERTICAL
        setPadding(dp(16), dp(16), dp(16), dp(16))
        setBackgroundColor(PANEL)
    }

    private fun label(value: String, size: Int, color: Int, bold: Boolean) =
        TextView(this).apply {
            text = value
            textSize = size.toFloat()
            setTextColor(color)
            if (bold) setTypeface(typeface, android.graphics.Typeface.BOLD)
        }

    private fun actionButton(title: String, action: () -> Unit) =
        Button(this).apply {
            text = title
            isAllCaps = false
            setTextColor(Color.WHITE)
            setBackgroundColor(ACCENT_DARK)
            setOnClickListener { action() }
        }

    private fun space(height: Int) = View(this).apply {
        layoutParams = LinearLayout.LayoutParams(1, dp(height))
    }

    private fun dp(value: Int): Int = (value * resources.displayMetrics.density).toInt()

    companion object {
        private const val REQUEST_GAME = 4102
        private const val REQUEST_BIOS = 4103
        private const val PREFS = "emucraft_library"
        private const val KEY_GAME_URI = "game_uri"
        private const val KEY_BIOS_URI = "bios_uri"
        private const val KEY_GAME_PATH = "game_private_path"
        private const val KEY_BIOS_PATH = "bios_private_path"
        private val GAME_EXTENSIONS = setOf("iso", "chd", "cso", "bin")
        private val BIOS_EXTENSIONS = setOf("bin", "rom", "bios")
        private const val BG = 0xFF0C0F18.toInt()
        private const val PANEL = 0xFF191F2C.toInt()
        private const val ACCENT = 0xFF53C4AA.toInt()
        private const val ACCENT_DARK = 0xFF238574.toInt()
        private const val MUTED = 0xFF9AA4B2.toInt()
    }
}
