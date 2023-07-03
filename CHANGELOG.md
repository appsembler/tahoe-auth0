# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

<!-- Note: Update the `Unreleased link` after adding a new release -->

## Unreleased

## 2.5.1 - 2023-07-03
 - Allow 404 to IdP user patch API for superusers

## 2.5.0 - 2023-06-29
 - Catch exceptions trying to get a tahoe idp uid for users

## 2.4.4 - 2023-06-28
 - Fix user_sync_to_idp receiver for UserProfile

## 2.4.3 - 2023-06-26
 - Check if Tahoe IdP enabled in config (avoid running in unrelated tests)

## 2.4.2 - 2023-06-23
 - Fix User, UserProfile save signals handler fields access

## 2.4.1 - 2023-06-22
 - Fix module import of student.models for signal handler

## 2.4.0 - 2023-06-22
 - Signal handler for User and UserProfile post_save to sync new values to fields in IdP

## 2.3.0 - 2023-04-19
 - Support retries to IdP API to get username

## 2.2.0 - 2023-01-02
 - Support for `idp_hint` URL parameter

## 2.1.0 - 2022-09-23
 - Support for `course_author` Studio-only role

## 2.0.0
 - TODO: Add release notes from GitHub releases

## 1.2.5
 - TODO: Add release notes from GitHub releases

## 1.2.4
 - TODO: Add release notes from GitHub releases

## 1.2.3
 - TODO: Add release notes from GitHub releases

## 1.2.2
 - TODO: Add release notes from GitHub releases

## 1.2.1
 - TODO: Add release notes from GitHub releases

## 1.1.0
 - TODO: Add release notes from GitHub releases

## 0.1.0-dev3
 - TODO: Add release notes from GitHub releases
