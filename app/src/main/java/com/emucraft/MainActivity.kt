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
import java.util.Locale

class MainActivity : Activity() {
    private lateinit var gameLabel: TextView
    private lateinit var biosLabel: TextView
    private lateinit var engineStatus: TextView
    private var gameUri: Uri? = null
    private var biosUri: Uri? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        window.statusBarColor = BG
        window.navigationBarColor = BG

        val prefs = getSharedPreferences(PREFS, MODE_PRIVATE)
        gameUri = prefs.getString(KEY_GAME_URI, null)?.let(Uri::parse)
        biosUri = prefs.getString(KEY_BIOS_URI, null)?.let(Uri::parse)

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
            "Game and BIOS selection are now stored on this device. Emulation is still disabled until a compatible PS2 core is integrated and tested.",
            13, Color.WHITE, false
        ).apply { setPadding(0, dp(8), 0, 0) })
        content.addView(note)
        content.addView(space(22))

        content.addView(label("DEVELOPMENT ROADMAP", 12, MUTED, true))
        listOf(
            "✓ Android ARM64 build foundation",
            "✓ Native C++ bridge and file selection",
            "✓ Persistent game / BIOS file references",
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
        val name = queryDisplayName(uri)
        val extension = name.substringAfterLast('.', "").lowercase(Locale.ROOT)

        val accepted = when (requestCode) {
            REQUEST_GAME -> extension in GAME_EXTENSIONS
            REQUEST_BIOS -> extension in BIOS_EXTENSIONS
            else -> false
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
            val flags = data.flags and (Intent.FLAG_GRANT_READ_URI_PERMISSION or Intent.FLAG_GRANT_WRITE_URI_PERMISSION)
            contentResolver.takePersistableUriPermission(uri, flags and Intent.FLAG_GRANT_READ_URI_PERMISSION)
        } catch (_: SecurityException) {
            // Some document providers grant only temporary access; selection still remains visible.
        }

        val prefs = getSharedPreferences(PREFS, MODE_PRIVATE)
        if (requestCode == REQUEST_GAME) {
            gameUri = uri
            prefs.edit().putString(KEY_GAME_URI, uri.toString()).apply()
            engineStatus.text = "Game file registered. The PS2 core is not connected yet."
        } else if (requestCode == REQUEST_BIOS) {
            biosUri = uri
            prefs.edit().putString(KEY_BIOS_URI, uri.toString()).apply()
            engineStatus.text = "BIOS reference saved. BIOS validation will be performed by the PS2 core."
        }
        refreshFileLabels()
    }

    private fun refreshFileLabels() {
        gameLabel.text = gameUri?.let { "Selected: ${queryDisplayName(it)}" } ?: "No PS2 game selected"
        biosLabel.text = biosUri?.let { "Selected: ${queryDisplayName(it)}" } ?: "No BIOS selected"
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
        private val GAME_EXTENSIONS = setOf("iso", "chd", "cso", "bin")
        private val BIOS_EXTENSIONS = setOf("bin", "rom", "bios")
        private const val BG = 0xFF0C0F18.toInt()
        private const val PANEL = 0xFF191F2C.toInt()
        private const val ACCENT = 0xFF53C4AA.toInt()
        private const val ACCENT_DARK = 0xFF238574.toInt()
        private const val MUTED = 0xFF9AA4B2.toInt()
    }
}
