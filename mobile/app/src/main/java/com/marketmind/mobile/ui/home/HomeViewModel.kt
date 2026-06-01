package com.marketmind.mobile.ui.home

import androidx.lifecycle.ViewModel
import com.marketmind.mobile.data.repository.AuthRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import javax.inject.Inject

@HiltViewModel
class HomeViewModel @Inject constructor(
    private val repository: AuthRepository,
) : ViewModel() {

    val nombre: String? = repository.getNombre()
    val role: String? = repository.getRole()

    fun logout() {
        repository.logout()
    }
}
