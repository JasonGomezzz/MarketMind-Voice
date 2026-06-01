package com.marketmind.mobile.di

import javax.inject.Qualifier

@Qualifier
@Retention(AnnotationRetention.BINARY)
annotation class AuthHttp

@Qualifier
@Retention(AnnotationRetention.BINARY)
annotation class ApiHttp

@Qualifier
@Retention(AnnotationRetention.BINARY)
annotation class SpringHttp
