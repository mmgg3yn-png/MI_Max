package com.mimax.lu

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL

/** OpenAI-compatible chat completions client. HTTPS is required to protect API credentials. */
class LauncherAiClient {
    suspend fun complete(endpoint: String, model: String, apiKey: String, prompt: String): Result<String> =
        withContext(Dispatchers.IO) {
            runCatching {
                require(endpoint.startsWith("https://")) { "AI endpoint must use HTTPS." }
                require(model.isNotBlank()) { "Enter a model ID in Settings." }
                require(apiKey.isNotBlank()) { "Enter your API key in Settings." }
                val url = URL(endpoint.trim())
                val connection = (url.openConnection() as HttpURLConnection).apply {
                    requestMethod = "POST"
                    connectTimeout = 20000
                    readTimeout = 60000
                    doOutput = true
                    setRequestProperty("Content-Type", "application/json")
                    setRequestProperty("Authorization", "Bearer $apiKey")
                }
                try {
                    val body = JSONObject()
                        .put("model", model)
                        .put("messages", JSONArray().put(JSONObject().put("role", "user").put("content", prompt)))
                    connection.outputStream.use { it.write(body.toString().toByteArray(Charsets.UTF_8)) }
                    val code = connection.responseCode
                    val stream = if (code in 200..299) connection.inputStream else connection.errorStream
                    val raw = stream?.bufferedReader()?.use { it.readText() }.orEmpty()
                    if (code !in 200..299) {
                        val message = runCatching { JSONObject(raw).optJSONObject("error")?.optString("message") }.getOrNull()
                        error(message?.takeIf { it.isNotBlank() } ?: "AI server returned HTTP $code")
                    }
                    val root = JSONObject(raw)
                    root.getJSONArray("choices").getJSONObject(0)
                        .getJSONObject("message").getString("content")
                } finally {
                    connection.disconnect()
                }
            }
        }
}
