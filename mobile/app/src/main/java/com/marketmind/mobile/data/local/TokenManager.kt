package com.marketmind.mobile.data.local

import android.content.Context
import android.content.SharedPreferences
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKeys
import dagger.hilt.android.qualifiers.ApplicationContext
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class TokenManager @Inject constructor(
    @ApplicationContext context: Context,
) {

    private val prefs: SharedPreferences by lazy {
        try {
            val masterKeyAlias = MasterKeys.getOrCreate(MasterKeys.AES256_GCM_SPEC)
            EncryptedSharedPreferences.create(
                "marketmind_secure_prefs",
                masterKeyAlias,
                context,
                EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
                EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM,
            )
        } catch (e: Exception) {
            // Fallback: si el keystore falla (emulador sin hardware),
            // usa SharedPreferences normales solo en debug.
            context.getSharedPreferences("marketmind_prefs_fallback",
                Context.MODE_PRIVATE)
        }
    }

    fun saveSession(access: String, refresh: String, role: String, nombre: String) {
        prefs.edit()
            .putString(KEY_ACCESS, access)
            .putString(KEY_REFRESH, refresh)
            .putString(KEY_ROLE, role)
            .putString(KEY_NOMBRE, nombre)
            .apply()
    }

    fun updateTokens(access: String, refresh: String?) {
        prefs.edit()
            .putString(KEY_ACCESS, access)
            .apply {
                if (!refresh.isNullOrBlank()) putString(KEY_REFRESH, refresh)
            }
            .apply()
    }

    fun getAccessToken(): String? = prefs.getString(KEY_ACCESS, null)
    fun getRefreshToken(): String? = prefs.getString(KEY_REFRESH, null)
    fun getRole(): String? = prefs.getString(KEY_ROLE, null)
    fun getNombre(): String? = prefs.getString(KEY_NOMBRE, null)

    fun isLoggedIn(): Boolean = !getAccessToken().isNullOrBlank()

    fun clear() {
        prefs.edit().clear().apply()
    }

    private companion object {
        const val PREFS_FILE_NAME = "marketmind_secure_prefs"
        const val KEY_ACCESS = "access_token"
        const val KEY_REFRESH = "refresh_token"
        const val KEY_ROLE = "role"
        const val KEY_NOMBRE = "nombre"
    }
}
