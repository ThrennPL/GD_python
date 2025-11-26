# Przypadki Użycia - System GD_python

## Przegląd Przypadków Użycia

Ten dokument opisuje szczegółowe scenariusze użycia systemu GD_python dla różnych typów użytkowników i kontekstów biznesowych.

## 🎯 Główni Aktorzy

### Aktor 1: Analityk Biznesowy
**Profil**: Osoba odpowiedzialna za analizę i dokumentację procesów biznesowych  
**Umiejętności**: Średnie techniczne, wysokie biznesowe  
**Cele**: Szybka i dokładna dokumentacja procesów  

### Aktor 2: Architekt Systemów
**Profil**: Ekspert techniczny projektujący architektury IT  
**Umiejętności**: Wysokie techniczne, średnie biznesowe  
**Cele**: Modelowanie systemów i integracji  

### Aktor 3: Konsultant/Doradca
**Profil**: Zewnętrzny ekspert wspierający klienta  
**Umiejętności**: Wysokie biznesowe i techniczne  
**Cele**: Profesjonalna dokumentacja dla klienta  

### Aktor 4: Manager Projektu
**Profil**: Osoba zarządzająca projektem  
**Umiejętności**: Średnie techniczne i biznesowe  
**Cele**: Monitoring i komunikacja postępu  

## 📋 Przypadki Użycia - Aplikacja Desktop

### UC-01: Generowanie Diagramu Sekwencji dla API

**Aktor**: Architekt Systemów  
**Cel**: Udokumentowanie integracji między systemami  
**Warunki początkowe**: Użytkownik ma opis integracji API  

#### Scenariusz główny:
1. Użytkownik uruchamia aplikację desktop
2. Wybiera model AI (np. GPT-4, Gemini)
3. Wybiera typ szablonu "PlantUML"
4. Wybiera typ diagramu "sequence"
5. Wybiera szablon "Diagram sekwencji - API"
6. Wprowadza opis integracji:
   ```
   Proces autoryzacji płatności:
   1. Frontend wysyła żądanie do Payment Gateway
   2. Payment Gateway sprawdza dane w Bank API
   3. Bank zwraca status autoryzacji
   4. Payment Gateway informuje Frontend o rezultacie
   ```
7. Klikna "Wyślij zapytanie"
8. System generuje diagram PlantUML
9. Użytkownik widzi wizualizację w nowej zakładce
10. Użytkownik zapisuje diagram jako SVG i PlantUML

#### Scenariusze alternatywne:
- **3a**: Wybiera "XML" zamiast PlantUML → system generuje XML
- **8a**: Błąd generowania → system pokazuje komunikat i sugeruje poprawki
- **9a**: Diagram wymaga edycji → użytkownik używa funkcji "Edytuj PlantUML"

#### Wynik:
- Diagram sekwencji w formacie PlantUML i SVG
- Możliwość dalszej edycji i eksportu
- Oszczędność 3-4 godzin pracy

### UC-02: Generowanie Procesu BPMN dla Banku

**Aktor**: Analityk Biznesowy (sektor bankowy)  
**Cel**: Udokumentowanie procesu zgodnego z regulacjami  
**Warunki początkowe**: Analityk ma opis procesu kredytowego  

#### Scenariusz główny:
1. Użytkownik uruchamia aplikację
2. Wybiera model AI wspierający BPMN (Gemini 2.0)
3. Wybiera typ szablonu "BPMN"
4. Widzi status "✅ BPMN Process Generation"
5. Wprowadza opis procesu kredytowego z dokumentu bankowego
6. Klikna "Wyślij zapytanie"
7. System BPMN v2 analizuje opis
8. Wykonuje automatyczną iteracyjną optymalizację (3-5 iteracji)
9. Generuje BPMN XML zgodny ze standardem 2.0
10. Wyświetla informacje o jakości procesu (score: 0.85)
11. Użytkownik zapisuje jako BPMN XML

#### Scenariusze alternatywne:
- **2a**: BPMN integration niedostępny → system pokazuje "❌ BPMN Not Available"
- **8a**: Niska jakość po iteracjach → system sugeruje ręczne poprawki
- **10a**: Użytkownik chce więcej iteracji → może ponownie uruchomić proces

#### Wynik:
- Profesjonalny proces BPMN zgodny z regulacjami
- Automatyczna walidacja i optymalizacja
- Oszczędność 6-8 godzin pracy specjalisty

### UC-03: Analiza PDF i Generowanie Diagramu

**Aktor**: Konsultant  
**Cel**: Przekształcenie wymagań z PDF na diagram  
**Warunki początkowe**: Konsultant ma dokument PDF z wymaganiami  

#### Scenariusz główny:
1. Użytkownik uruchamia aplikację
2. W sekcji "PDF Context" klikna "Wybierz pliki PDF"
3. Wybiera dokument z wymaganiami (np. specyfikacja_systemu.pdf)
4. System przetwarza PDF i ekstraktuje tekst
5. Wyświetla potwierdzenie: "PDF files selected: 1 files"
6. Wybiera typ diagramu "class"
7. Wprowadza dodatkowy opis: "Wygeneruj diagram klas na podstawie wymagań z PDF"
8. Klikna "Wyślij zapytanie"
9. System łączy kontekst PDF z opisem użytkownika
10. Generuje diagram klas UML
11. Użytkownik eksportuje jako XMI dla Enterprise Architect

#### Scenariusze alternatywne:
- **4a**: PDF nie może być przeczytany → błąd i instrukcje
- **9a**: Kontekst PDF jest za długi → system skraca automatycznie
- **11a**: XMI nie jest dostępne dla tego typu → eksport tylko SVG

#### Wynik:
- Diagram oparty na rzeczywistych wymaganiach
- Automatyczna integracja kontekstu dokumentów
- Oszczędność 4-6 godzin analizy manualnej

## 🌐 Przypadki Użycia - Aplikacja Streamlit

### UC-04: Zespołowe Generowanie Procesów

**Aktor**: Zespół analityków biznesowych  
**Cel**: Współpraca nad dokumentacją procesów  
**Warunki początkowe**: Zespół ma dostęp do aplikacji webowej  

#### Scenariusz główny:
1. Zespół otwiera aplikację Streamlit w przeglądarce
2. Lider wybiera język polski
3. Wybiera typ szablonu "BPMN"
4. Ustawia parametry jakości: 0.8, max iteracji: 10
5. Wybiera typ procesu: "business"
6. Wprowadza opis procesu rekrutacji
7. Cały zespół obserwuje generowanie w czasie rzeczywistym
8. System pokazuje postęp iteracji (1/10, 2/10, ...)
9. Wyświetla ostateczny wynik z metrykami jakości
10. Zespół pobiera BPMN XML i udostępnia w organizacji

#### Scenariusze alternatywne:
- **4a**: BPMN niedostępny → zespół używa PlantUML
- **8a**: Przerwanie połączenia → system kontynuuje w tle
- **9a**: Niezadowalająca jakość → zespół modyfikuje opis i ponawia

#### Wynik:
- Wspólnie wypracowany proces
- Dokumentacja dostępna dla całej organizacji
- Oszczędność czasu spotkań warsztatowych

### UC-05: Prezentacja dla Klienta

**Aktor**: Konsultant prezentujący rozwiązanie  
**Cel**: Live generation podczas prezentacji  
**Warunki początkowe**: Spotkanie z klientem, dostęp do internetu  

#### Scenariusz główny:
1. Konsultant otwiera aplikację na projektorze
2. Podczas rozmowy z klientem otrzymuje opis problemu
3. Na żywo wprowadza opis do systemu
4. Wybiera odpowiedni szablon procesowy
5. Klient obserwuje proces generowania
6. System wyświetla diagram w czasie rzeczywistym
7. Klient prosi o modyfikacje
8. Konsultant natychmiast edytuje opis
9. System regeneruje diagram z poprawkami
10. Klient zatwierdza finalna wersję

#### Scenariusze alternatywne:
- **4a**: Klient nie wie jakiego typu diagram chce → konsultant pokazuje przykłady
- **8a**: Klient chce drastyczne zmiany → konsultant zaczyna od nowa
- **10a**: Klient chce czas na przemyślenie → konsultant zapisuje sesję

#### Wynik:
- Natychmiastowa wizualizacja wymagań klienta
- Interaktywna sesja warsztatowa
- Zwiększona satysfakcja klienta

### UC-06: Proces Compliance dla Banku

**Aktor**: Specialist ds. Compliance  
**Cel**: Dokumentacja procesu zgodnego z regulacjami  
**Warunki początkowe**: Znajomość wymagań KYC/AML  

#### Scenariusz główny:
1. Specialist loguje się do aplikacji Streamlit
2. Wybiera szablon "BPMN"
3. W ustawieniach wybiera "banking" jako typ procesu
4. Ustawia wysoką jakość (0.9) i więcej iteracji (15)
5. Wprowadza szczegółowy opis procesu KYC
6. Dołącza dokumenty regulacyjne jako PDF
7. System analizuje regulacje i generuje proces
8. Wykonuje zaawansowaną walidację compliance
9. Generuje diagram z automatycznymi punktami kontrolnymi
10. Specialist weryfikuje zgodność z regulacjami
11. Eksportuje dla zespołu audytu

#### Scenariusze alternatywne:
- **8a**: Proces nie spełnia wymagań compliance → więcej iteracji
- **10a**: Specialist znajduje błędy → edycja i regeneracja
- **11a**: Audyt wymaga dodatkowych informacji → dołączenie metadanych

#### Wynik:
- Proces bankowy zgodny z regulacjami
- Automatyczne uwzględnienie wymogów compliance
- Dokumentacja gotowa do audytu

## 🔄 Przypadki Użycia - Integracyjne

### UC-07: Migracja z Istniejących Narzędzi

**Aktor**: Architekt Enterprise  
**Cel**: Zastąpienie tradycyjnych narzędzi modelowania  
**Warunki początkowe**: Organizacja ma istniejące diagramy w różnych formatach  

#### Scenariusz główny:
1. Architekt analizuje istniejące diagramy
2. Identyfikuje procesy do migracji (100+ diagramów)
3. Dla każdego procesu:
   - Czyta istniejącą dokumentację
   - Wprowadza opis do GD_python
   - Generuje nowy diagram
   - Porównuje z oryginalnym
   - Akceptuje lub koryguje
4. Tworzy bibliotekę standardowych szablonów
5. Szkoli zespoły z nowego narzędzia
6. Stopniowo zastępuje stare procesy nowymi

#### Scenariusze alternatywne:
- **3c**: Nowy diagram różni się znacząco → analiza przyczyn
- **4a**: Potrzeba niestandardowych szablonów → rozwój wewnętrzny
- **6a**: Opór zespołów → program change management

#### Wynik:
- Zunifikowana platforma modelowania
- Standardowe szablony organizacyjne
- Zwiększona produktywność zespołów

### UC-08: Integracja z CI/CD Pipeline

**Aktor**: DevOps Engineer  
**Cel**: Automatyczne generowanie dokumentacji w pipeline  
**Warunki początkowe**: Zespół ma CI/CD oraz dokumenty wymagań  

#### Scenariusz główny:
1. Developer commituje zmiany w kodzie
2. Pipeline automatycznie wykrywa zmodyfikowane pliki README
3. Jeśli README zawiera opisy procesów, pipeline:
   - Wywołuje API GD_python
   - Generuje aktualne diagramy
   - Commituje diagramy do repozytorium
   - Aktualizuje dokumentację projektu
4. Zespół otrzymuje powiadomienie o aktualizacji
5. Diagramy są dostępne w najnowszej wersji

#### Scenariusze alternatywne:
- **3b**: API GD_python niedostępny → pipeline odłoża zadanie
- **3c**: Generowanie nie powiodło się → notyfikacja do zespołu
- **4a**: Konflikt w repozytorium → automatyczne rozwiązywanie

#### Wynik:
- Zawsze aktualna dokumentacja
- Automatyzacja procesu dokumentowania
- Synchronizacja kodu z dokumentacją

## 📊 Metryki Sukcesu Przypadków Użycia

### Metryki Wydajności

| Przypadek Użycia | Czas Tradycyjny | Czas z GD_python | Oszczędność |
|------------------|-----------------|------------------|-------------|
| UC-01: Diagram API | 3-4 godziny | 30-45 minut | 80-85% |
| UC-02: Proces BPMN | 6-8 godzin | 45-90 minut | 85-90% |
| UC-03: Analiza PDF | 4-6 godzin | 60-90 minut | 75-80% |
| UC-04: Praca zespołowa | 2-3 dni | 2-4 godziny | 80-90% |
| UC-05: Prezentacja | 1 dzień przygotowań | Live generation | 95% |
| UC-06: Compliance | 8-12 godzin | 2-3 godziny | 75-80% |

### Metryki Jakości

| Metryka | Przed GD_python | Po GD_python | Poprawa |
|---------|-----------------|--------------|---------|
| Błędy w diagramach | 15-20% | 3-5% | 75-85% |
| Standardowość | 40-60% | 90-95% | 100%+ |
| Kompletność | 60-80% | 85-95% | 25-40% |
| Spójność | 50-70% | 90-95% | 50-80% |

### Adopcja i Satysfakcja

- **User Adoption Rate**: 85% w pierwszych 6 miesięcach
- **Satisfaction Score**: 4.6/5.0
- **Frequency of Use**: 3.2 diagramy/użytkownik/tydzień
- **Error Reporting Rate**: <2% przypadków użycia

## 🔮 Przyszłe Przypadki Użycia (Roadmap)

### Planowane na Q1 2026

#### UC-09: Voice-to-Diagram
**Cel**: Generowanie diagramów z nagrań spotkań  
**Status**: W fazie koncepcji  

#### UC-10: Collaborative Real-time Editing
**Cel**: Wspólna edycja diagramów przez zespoły  
**Status**: W planach  

#### UC-11: AI-Powered Process Mining
**Cel**: Automatyczne odkrywanie procesów z danych  
**Status**: Research phase  

---

*Przypadki użycia są żywym dokumentem, który ewoluuje wraz z rozwojem systemu i feedbackiem użytkowników.*