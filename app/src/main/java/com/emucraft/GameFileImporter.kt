package com.emucraft

import android.content.ContentResolver
import android.net.Uri
import java.io.File
import java.io.FileOutputStream
import java.io.IOException
import java.security.MessageDigest
import java.util.Locale

/**
 * Copies SAF-selected content into app-private storage.
 *
 * The native emulator core will need ordinary filesystem paths; content:// URIs
 * are not paths and may become unreadable when a provider revokes temporary access.
 */
object GameFileImporter {
    data class ImportedFile(
        val file: File,
        val sizeBytes: Long,
        val sha256: String
    )

    @Throws(IOException::class)
    fun importFile(
        resolver: ContentResolver,
        uri: Uri,
        displayName: String,
        kind: String,
        filesDirectory: File
    ): ImportedFile {
        require(kind == "game" || kind == "bios") { "Unsupported import type." }

        val importDirectory = File(filesDirectory, "emucraft/imports")
        if (!importDirectory.exists() && !importDirectory.mkdirs()) {
            throw IOException("Could not create the private import directory.")
        }
        if (!importDirectory.isDirectory) {
            throw IOException("The private import path is not a directory.")
        }

        val safeName = displayName
            .substringAfterLast('/')
            .replace(Regex("[^A-Za-z0-9._-]"), "_")
            .trim('_')
            .takeLast(80)
            .ifBlank { if (kind == "bios") "bios.bin" else "game.iso" }

        val temporary = File(importDirectory, ".$kind-${System.nanoTime()}.part")
        val digest = MessageDigest.getInstance("SHA-256")
        var copiedBytes = 0L

        try {
            val input = resolver.openInputStream(uri)
                ?: throw IOException("Android could not open the selected document.")

            input.use { source ->
                FileOutputStream(temporary).use { destination ->
                    val buffer = ByteArray(DEFAULT_BUFFER_SIZE)
                    while (true) {
                        val count = source.read(buffer)
                        if (count < 0) break
                        if (count == 0) continue
                        destination.write(buffer, 0, count)
                        digest.update(buffer, 0, count)
                        copiedBytes += count.toLong()
                    }
                    destination.fd.sync()
                }
            }

            if (copiedBytes == 0L) {
                throw IOException("The selected file is empty.")
            }

            val hash = digest.digest().joinToString("") { "%02x".format(Locale.ROOT, it.toInt() and 0xff) }
            val finalFile = File(importDirectory, "${kind}_${hash.take(16)}_${safeName}")

            if (finalFile.exists()) {
                if (finalFile.length() != copiedBytes) {
                    throw IOException("A file-name collision was detected; import was stopped safely.")
                }
                temporary.delete()
            } else if (!temporary.renameTo(finalFile)) {
                throw IOException("Could not finalize the imported file.")
            }

            return ImportedFile(finalFile, copiedBytes, hash)
        } catch (error: Exception) {
            temporary.delete()
            if (error is IOException) throw error
            throw IOException("Import failed: ${error.message ?: error.javaClass.simpleName}", error)
        }
    }
}
