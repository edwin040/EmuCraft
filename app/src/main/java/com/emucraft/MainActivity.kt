package com.emucraft

import android.app.Activity
import android.content.Intent
import android.graphics.Color
import android.net.Uri
import android.os.Bundle
import android.view.ViewGroup
import android.widget.Button
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView

class MainActivity : Activity() {
    private lateinit var selectedFile: TextView
    private lateinit var engineStatus: TextView
    private var selectedUri: Uri? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        window.statusBarColor = Color.rgb(12, 15, 24)
        window.navigationBarColor = Color.rgb(12, 15, 24)

        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(24, 28, 24, 24)
            setBackgroundColor(Color.rgb(12, 15, 24))
        }
        val scroll = ScrollView(this)
        val content = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(0, 0, 0, 24)
        }

        content.addView(text("EMUCRAFT", 13, 0xFF53C4AA.toInt(), true))
        content.addView(text("PS2 Emulator", 30, Color.WHITE, true).apply { setPadding(0, 8, 0, 4) })
        content.addView(text("Android • Performance-first • ARM64", 13, 0xFF9AA4B2.toInt(), false))
        content.addView(gap(28))

        val panel = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(18, 18, 18, 18)
            setBackgroundColor(Color.rgb(25, 31, 44))
        }
        panel.addView(text("PROJECT STATUS", 11, 0xFF53C4AA.toInt(), true))
        engineStatus = text("Application shell ready. PS2 engine integration is not yet included.", 15, Color.WHITE, false)
        engineStatus.setPadding(0, 12, 0, 0)
        panel.addView(engineStatus)
        content.addView(panel)
        content.addView(gap(24))

        content.addView(text("GAME LIBRARY", 12, 0xFF9AA4B2.toInt(), true))
        selectedFile = text("No game selected", 15, Color.WHITE, false).apply { setPadding(0, 14, 0, 14) }
        content.addView(selectedFile)
        content.addView(actionButton("Choose PS2 ISO") { openGamePicker() })
        content.addView(gap(20))

        content.addView(text("NEXT DEVELOPMENT STEPS", 12, 0xFF9AA4B2.toInt(), true))
        listOf(
            "01  Android + ARM64 build foundation",
            "02  PS2 core feasibility and licensing review",
            "03  BIOS and game-file management",
            "04  Vulkan renderer and audio pipeline",
            "05  Controller, memory card and save states"
        ).forEach { content.addView(text(it, 14, Color.WHITE, false).apply { setPadding(0, 10, 0, 10) }) }

        scroll.addView(content)
        root.addView(scroll, LinearLayout.LayoutParams(-1, 0, 1f))
        setContentView(root)
    }

    private fun openGamePicker() {
        val intent = Intent(Intent.ACTION_OPEN_DOCUMENT).apply {
            addCategory(Intent.CATEGORY_OPENABLE)
            type = "*/*"
        }
        startActivityForResult(intent, REQUEST_GAME)
    }

    @Deprecated("Uses Android Storage Access Framework for user-selected game files.")
    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (requestCode == REQUEST_GAME && resultCode == RESULT_OK) {
            data?.data?.let { uri ->
                selectedUri = uri
                try {
                    contentResolver.takePersistableUriPermission(uri, Intent.FLAG_GRANT_READ_URI_PERMISSION)
                } catch (_: SecurityException) { }
                selectedFile.text = "Selected file:\n${uri.lastPathSegment ?: uri}"
                engineStatus.text = "File selected. Game execution is not available until a compatible PS2 core is integrated."
            }
        }
    }

    private fun text(value: String, size: Int, color: Int, bold: Boolean) =
        TextView(this).apply {
            text = value
            textSize = size.toFloat()
            setTextColor(color)
            if (bold) setTypeface(typeface, android.graphics.Typeface.BOLD)
        }

    private fun gap(height: Int) = TextView(this).apply { this.height = height }

    private fun actionButton(label: String, action: () -> Unit) =
        Button(this).apply {
            text = label
            isAllCaps = false
            setTextColor(Color.WHITE)
            setBackgroundColor(Color.rgb(35, 133, 116))
            setOnClickListener { action() }
        }

    companion object { private const val REQUEST_GAME = 4102 }
}
