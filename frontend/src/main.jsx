import React, { useEffect, useMemo, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import './styles.css';

const PHONE_DISPLAY = '+1 888 707 8012';
const PHONE_TEL = '+1' + '8887078012';

const SERVICE_FALLBACK = [
  { service_id: 'cardiac_surgery', service_label: 'Cardiac surgery', specialty_group: 'Cardiology / CTVS' },
  { service_id: 'eye_care', service_label: 'Eye surgery / eye care', specialty_group: 'Ophthalmology' },
  { service_id: 'icu_critical_care', service_label: 'ICU / critical care', specialty_group: 'Critical Care' },
  { service_id: 'dialysis', service_label: 'Dialysis', specialty_group: 'Nephrology' },
  { service_id: 'oncology', service_label: 'Oncology', specialty_group: 'Oncology' },
  { service_id: 'maternity_obgyn', service_label: 'Maternity / OBGYN', specialty_group: 'Maternity / OBGYN' },
  { service_id: 'emergency_trauma', service_label: 'Emergency / trauma', specialty_group: 'Emergency / Trauma' },
];

const TABS = [
  { id: 'explorer', labelKey: 'facilityExplorer' },
  { id: 'map', labelKey: 'geoSearch' },
  { id: 'verification', labelKey: 'trustReview' },
  { id: 'assistant', labelKey: 'chatAssistant' },
];

const LANGUAGES = [
  { code: 'en', label: 'English' },
  { code: 'hi', label: 'हिन्दी' },
  { code: 'te', label: 'తెలుగు' },
];

const I18N = {
  en: {
    appLanguage: 'Language', facilityExplorer: 'Facility Explorer', geoSearch: 'Geo Search', trustReview: 'Trust Review', chatAssistant: '💬 Chat Assistant',
    mainSections: 'Main sections', brandSub: 'Facility Trust Desk - Trust Starts Here', callAria: 'Call {phone}', mission: 'CareSignal helps people find trusted facilities for healthier lives',
    country: 'Country', allCountries: 'All Countries', stateRegion: 'State / Region', allStates: 'All States', city: 'City', allCities: 'All Cities', allCitiesInState: 'All Cities In State', postalCode: 'Postal Code', allPostalCodes: 'All Postal Codes', procedure: 'Procedure', radius: 'Radius', selectProcedures: 'Select Procedures', proceduresSelected: '{count} Procedures Selected',
    rankedFacilities: 'Ranked Facilities', rank: 'Rank', facility: 'Facility', facilityName: 'Facility Name', location: 'Location', confidencePct: 'Confidence %', trustTier: 'Trust Tier', evidence: 'Evidence', allLocations: 'All Locations', confidence: 'Confidence', all: 'All', high: 'High', medium: 'Medium', needsReview: 'Needs Review', verified: 'Verified', clickHere: 'Click Here', noFacilities: 'No Facilities Match These Table Filters.',
    trustCard: 'Facility Trust Card', locationPending: 'Location Pending', trustScore: 'Trust Score', claim: 'Claim:', supports: 'Supports {service}.', howScoreWorks: 'How Score Works', verifySourceLinks: 'Verify Source Links', verifying: 'Verifying…', agentBricksReview: 'Agent Bricks Review', specialties: 'Specialties', procedures: 'Procedures', equipmentServices: 'Equipment / Services', noSpecialties: 'No specialty claims extracted yet.', noProcedures: 'No procedure claims extracted yet.', scoreBreakdown: 'Score Breakdown', sources: 'Sources', noSourceUrl: 'No source URL available yet.', uncertainty: 'Uncertainty:', defaultUncertainty: 'Treat extracted claims as claims to verify, not ground truth.',
    googleMapsRadius: 'Google Maps Radius', insideRadius: '{count} facilities inside selected radius', viewTrustCard: 'View Trust Card', googleMapsUnavailable: 'Google Maps Unavailable', selectFacilityMap: 'Select a facility with latitude/longitude to load the map.',
    selectedFacility: 'Selected Facility', informationAsOf: 'Information As Of:', reviewReady: 'Review Ready', selectFacilityToReview: 'Select a facility to review.', openTrustCard: 'Open Trust Card', addToShortlist: 'Add to Shortlist', viewShortlist: 'View Shortlist ({count})', savedActions: 'Saved Actions: {actions} • Scenarios: {scenarios}', selectFacility: 'Select Facility',
    recentVerifications: 'Recent Verifications', recentUserActions: 'Recent User Actions', savedScenarios: 'Saved Scenarios', noVerificationHistory: 'No verification history yet.', noUserActions: 'No persisted notes, overrides, or review decisions yet.', noSavedScenarios: 'No saved scenarios yet.', readBackLakebase: 'Read Back From Lakebase',
    chatAssistantTitle: 'Chat Assistant', safeQueryTemplates: 'Safe Query Templates', generateAnswer: 'Generate Answer', topFacilitiesPrompt: 'Top {service} facilities', explainFacilityPrompt: 'Explain {facility}', claimsNeedVerificationPrompt: 'Which claims need verification?', defaultQuestion: 'Show top {service} facilities and explain evidence.', fallbackAnswer: 'Rankings combine evidence fields, sources, contactability, location completeness and human verification.',
    trustReviewActions: 'Trust Review Actions', datedInfo: 'Information shown here is dated. Use Verify Sources, Agent Bricks Review, or Call Facility to refresh what the next user sees.', callFacilityDemo: 'Call Facility (Demo)', calling: 'Calling…', serviceAvailable: 'Service Currently Available', equipmentConfirmed: 'Equipment/Facilities Confirmed', specialistsConfirmed: 'Specialists/Referral Pathway Confirmed', reviewStatus: 'Review Status:', addNotePlaceholder: 'Add note, e.g. This facility needs NICU verification', submitReview: 'Submit Review', reviewSubmitted: 'Review has been submitted.', overrideScorePlaceholder: 'Override score %, current {score}', saveScoreOverride: 'Save Score Override', reasonOverride: 'Reason for score override', scoreOverrideSaved: 'Score override saved.', scenarioPlaceholder: 'Scenario, e.g. {service} options in {location}', saveScenarios: 'Save Scenarios', scenarioSaved: 'Scenario saved.',
    latestFacilityInfo: 'Latest Facility Information', savedLakebaseInfo: 'Saved in Lakebase so future users see recent source checks, Agent Bricks reviews, reviews, overrides, and call notes.', noRecentUpdates: 'No recent updates yet. Use Verify Sources, Agent Bricks Review, or Call Facility to refresh this facility.',
  },
  hi: {
    appLanguage: 'भाषा', facilityExplorer: 'सुविधा खोज', geoSearch: 'भौगोलिक खोज', trustReview: 'विश्वास समीक्षा', chatAssistant: '💬 चैट सहायक',
    mainSections: 'मुख्य अनुभाग', brandSub: 'सुविधा विश्वास डेस्क - भरोसा यहीं से शुरू', callAria: '{phone} पर कॉल करें', mission: 'CareSignal लोगों को स्वस्थ जीवन के लिए भरोसेमंद सुविधाएँ खोजने में मदद करता है',
    country: 'देश', allCountries: 'सभी देश', stateRegion: 'राज्य / क्षेत्र', allStates: 'सभी राज्य', city: 'शहर', allCities: 'सभी शहर', allCitiesInState: 'राज्य के सभी शहर', postalCode: 'पिन कोड', allPostalCodes: 'सभी पिन कोड', procedure: 'प्रक्रिया', radius: 'दायरा', selectProcedures: 'प्रक्रियाएँ चुनें', proceduresSelected: '{count} प्रक्रियाएँ चयनित',
    rankedFacilities: 'रैंक की गई सुविधाएँ', rank: 'रैंक', facility: 'सुविधा', facilityName: 'सुविधा का नाम', location: 'स्थान', confidencePct: 'विश्वास %', trustTier: 'विश्वास स्तर', evidence: 'प्रमाण', allLocations: 'सभी स्थान', confidence: 'विश्वास', all: 'सभी', high: 'उच्च', medium: 'मध्यम', needsReview: 'समीक्षा आवश्यक', verified: 'सत्यापित', clickHere: 'यहाँ क्लिक करें', noFacilities: 'इन टेबल फ़िल्टर से कोई सुविधा मेल नहीं खाती।',
    trustCard: 'सुविधा विश्वास कार्ड', locationPending: 'स्थान लंबित', trustScore: 'विश्वास स्कोर', claim: 'दावा:', supports: '{service} समर्थित है।', howScoreWorks: 'स्कोर कैसे काम करता है', verifySourceLinks: 'स्रोत लिंक सत्यापित करें', verifying: 'सत्यापित हो रहा है…', agentBricksReview: 'एजेंट ब्रिक्स समीक्षा', specialties: 'विशेषताएँ', procedures: 'प्रक्रियाएँ', equipmentServices: 'उपकरण / सेवाएँ', noSpecialties: 'अभी कोई विशेषता दावा नहीं मिला।', noProcedures: 'अभी कोई प्रक्रिया दावा नहीं मिला।', scoreBreakdown: 'स्कोर विवरण', sources: 'स्रोत', noSourceUrl: 'अभी कोई स्रोत URL उपलब्ध नहीं है।', uncertainty: 'अनिश्चितता:', defaultUncertainty: 'निकाले गए दावों को सत्यापन योग्य दावे मानें, अंतिम सत्य नहीं।',
    googleMapsRadius: 'Google Maps दायरा', insideRadius: 'चुने गए दायरे में {count} सुविधाएँ', viewTrustCard: 'विश्वास कार्ड देखें', googleMapsUnavailable: 'Google Maps उपलब्ध नहीं', selectFacilityMap: 'मैप लोड करने के लिए अक्षांश/देशांतर वाली सुविधा चुनें।',
    selectedFacility: 'चयनित सुविधा', informationAsOf: 'जानकारी दिनांक:', reviewReady: 'समीक्षा तैयार', selectFacilityToReview: 'समीक्षा के लिए सुविधा चुनें।', openTrustCard: 'विश्वास कार्ड खोलें', addToShortlist: 'शॉर्टलिस्ट में जोड़ें', viewShortlist: 'शॉर्टलिस्ट देखें ({count})', savedActions: 'सहेजी गई कार्रवाइयाँ: {actions} • परिदृश्य: {scenarios}', selectFacility: 'सुविधा चुनें',
    recentVerifications: 'हालिया सत्यापन', recentUserActions: 'हालिया उपयोगकर्ता कार्रवाइयाँ', savedScenarios: 'सहेजे गए परिदृश्य', noVerificationHistory: 'अभी कोई सत्यापन इतिहास नहीं।', noUserActions: 'अभी कोई सहेजे गए नोट, ओवरराइड या समीक्षा निर्णय नहीं।', noSavedScenarios: 'अभी कोई सहेजा गया परिदृश्य नहीं।', readBackLakebase: 'Lakebase से पढ़ा गया',
    chatAssistantTitle: 'चैट सहायक', safeQueryTemplates: 'सुरक्षित प्रश्न टेम्पलेट', generateAnswer: 'उत्तर बनाएँ', topFacilitiesPrompt: 'शीर्ष {service} सुविधाएँ', explainFacilityPrompt: '{facility} समझाएँ', claimsNeedVerificationPrompt: 'किन दावों का सत्यापन चाहिए?', defaultQuestion: 'शीर्ष {service} सुविधाएँ दिखाएँ और प्रमाण समझाएँ।', fallbackAnswer: 'रैंकिंग प्रमाण फ़ील्ड, स्रोत, संपर्कयोग्यता, स्थान पूर्णता और मानव सत्यापन को जोड़ती है।',
    trustReviewActions: 'विश्वास समीक्षा कार्रवाइयाँ', datedInfo: 'यह जानकारी दिनांकित है। अगले उपयोगकर्ता के लिए जानकारी ताज़ा करने हेतु स्रोत सत्यापित करें, एजेंट ब्रिक्स समीक्षा या सुविधा कॉल का उपयोग करें।', callFacilityDemo: 'सुविधा कॉल करें (डेमो)', calling: 'कॉल हो रही है…', serviceAvailable: 'सेवा अभी उपलब्ध', equipmentConfirmed: 'उपकरण/सुविधाएँ पुष्टि हुईं', specialistsConfirmed: 'विशेषज्ञ/रेफ़रल पथ पुष्टि हुआ', reviewStatus: 'समीक्षा स्थिति:', addNotePlaceholder: 'नोट जोड़ें, जैसे इस सुविधा को NICU सत्यापन चाहिए', submitReview: 'समीक्षा जमा करें', reviewSubmitted: 'समीक्षा जमा हो गई है।', overrideScorePlaceholder: 'स्कोर % बदलें, वर्तमान {score}', saveScoreOverride: 'स्कोर ओवरराइड सहेजें', reasonOverride: 'स्कोर ओवरराइड का कारण', scoreOverrideSaved: 'स्कोर ओवरराइड सहेजा गया।', scenarioPlaceholder: 'परिदृश्य, जैसे {location} में {service} विकल्प', saveScenarios: 'परिदृश्य सहेजें', scenarioSaved: 'परिदृश्य सहेजा गया।',
    latestFacilityInfo: 'नवीनतम सुविधा जानकारी', savedLakebaseInfo: 'Lakebase में सहेजा गया ताकि भविष्य के उपयोगकर्ता हालिया स्रोत जाँच, एजेंट समीक्षा, समीक्षा, ओवरराइड और कॉल नोट देख सकें।', noRecentUpdates: 'अभी कोई हालिया अपडेट नहीं। इस सुविधा को ताज़ा करने के लिए स्रोत सत्यापन, एजेंट समीक्षा या कॉल सुविधा का उपयोग करें।',
  },
  te: {
    appLanguage: 'భాష', facilityExplorer: 'సదుపాయాల అన్వేషణ', geoSearch: 'భౌగోళిక శోధన', trustReview: 'నమ్మకం సమీక్ష', chatAssistant: '💬 చాట్ అసిస్టెంట్',
    mainSections: 'ప్రధాన విభాగాలు', brandSub: 'సదుపాయ నమ్మకం డెస్క్ - నమ్మకం ఇక్కడ మొదలవుతుంది', callAria: '{phone}కి కాల్ చేయండి', mission: 'CareSignal ఆరోగ్యకరమైన జీవితాల కోసం నమ్మదగిన సదుపాయాలను కనుగొనడంలో ప్రజలకు సహాయపడుతుంది',
    country: 'దేశం', allCountries: 'అన్ని దేశాలు', stateRegion: 'రాష్ట్రం / ప్రాంతం', allStates: 'అన్ని రాష్ట్రాలు', city: 'నగరం', allCities: 'అన్ని నగరాలు', allCitiesInState: 'రాష్ట్రంలోని అన్ని నగరాలు', postalCode: 'పిన్ కోడ్', allPostalCodes: 'అన్ని పిన్ కోడ్‌లు', procedure: 'ప్రక్రియ', radius: 'వ్యాసార్థం', selectProcedures: 'ప్రక్రియలను ఎంచుకోండి', proceduresSelected: '{count} ప్రక్రియలు ఎంపికయ్యాయి',
    rankedFacilities: 'ర్యాంక్ చేసిన సదుపాయాలు', rank: 'ర్యాంక్', facility: 'సదుపాయం', facilityName: 'సదుపాయం పేరు', location: 'స్థానం', confidencePct: 'నమ్మకం %', trustTier: 'నమ్మకం స్థాయి', evidence: 'సాక్ష్యం', allLocations: 'అన్ని స్థానాలు', confidence: 'నమ్మకం', all: 'అన్నీ', high: 'అధికం', medium: 'మధ్యస్థం', needsReview: 'సమీక్ష అవసరం', verified: 'ధృవీకరించబడింది', clickHere: 'ఇక్కడ క్లిక్ చేయండి', noFacilities: 'ఈ టేబుల్ ఫిల్టర్‌లకు సరిపడే సదుపాయాలు లేవు.',
    trustCard: 'సదుపాయ నమ్మకం కార్డ్', locationPending: 'స్థానం పెండింగ్‌లో ఉంది', trustScore: 'నమ్మకం స్కోర్', claim: 'దావా:', supports: '{service}కు మద్దతు ఉంది.', howScoreWorks: 'స్కోర్ ఎలా పని చేస్తుంది', verifySourceLinks: 'మూల లింక్‌లను ధృవీకరించండి', verifying: 'ధృవీకరిస్తోంది…', agentBricksReview: 'ఏజెంట్ బ్రిక్స్ సమీక్ష', specialties: 'ప్రత్యేకతలు', procedures: 'ప్రక్రియలు', equipmentServices: 'పరికరాలు / సేవలు', noSpecialties: 'ఇంకా ప్రత్యేకత దావాలు లేవు.', noProcedures: 'ఇంకా ప్రక్రియ దావాలు లేవు.', scoreBreakdown: 'స్కోర్ విభజన', sources: 'మూలాలు', noSourceUrl: 'ఇంకా మూల URL అందుబాటులో లేదు.', uncertainty: 'అనిశ్చితి:', defaultUncertainty: 'తీసుకున్న దావాలను ధృవీకరించాల్సిన దావాలుగా పరిగణించండి, అంతిమ సత్యంగా కాదు.',
    googleMapsRadius: 'Google Maps వ్యాసార్థం', insideRadius: 'ఎంచుకున్న వ్యాసార్థంలో {count} సదుపాయాలు', viewTrustCard: 'నమ్మకం కార్డ్ చూడండి', googleMapsUnavailable: 'Google Maps అందుబాటులో లేదు', selectFacilityMap: 'మ్యాప్ లోడ్ చేయడానికి అక్షాంశం/రేఖాంశం ఉన్న సదుపాయాన్ని ఎంచుకోండి.',
    selectedFacility: 'ఎంచుకున్న సదుపాయం', informationAsOf: 'సమాచారం తేదీ:', reviewReady: 'సమీక్షకు సిద్ధం', selectFacilityToReview: 'సమీక్షించడానికి సదుపాయాన్ని ఎంచుకోండి.', openTrustCard: 'నమ్మకం కార్డ్ తెరవండి', addToShortlist: 'షార్ట్‌లిస్ట్‌కు జోడించండి', viewShortlist: 'షార్ట్‌లిస్ట్ చూడండి ({count})', savedActions: 'సేవ్ చేసిన చర్యలు: {actions} • సన్నివేశాలు: {scenarios}', selectFacility: 'సదుపాయం ఎంచుకోండి',
    recentVerifications: 'తాజా ధృవీకరణలు', recentUserActions: 'తాజా వినియోగదారు చర్యలు', savedScenarios: 'సేవ్ చేసిన సన్నివేశాలు', noVerificationHistory: 'ఇంకా ధృవీకరణ చరిత్ర లేదు.', noUserActions: 'ఇంకా సేవ్ చేసిన నోట్స్, ఓవర్‌రైడ్‌లు లేదా సమీక్ష నిర్ణయాలు లేవు.', noSavedScenarios: 'ఇంకా సేవ్ చేసిన సన్నివేశాలు లేవు.', readBackLakebase: 'Lakebase నుండి చదివింది',
    chatAssistantTitle: 'చాట్ అసిస్టెంట్', safeQueryTemplates: 'సురక్షిత ప్రశ్న టెంప్లేట్లు', generateAnswer: 'సమాధానం రూపొందించండి', topFacilitiesPrompt: 'అగ్ర {service} సదుపాయాలు', explainFacilityPrompt: '{facility} వివరించండి', claimsNeedVerificationPrompt: 'ఏ దావాలకు ధృవీకరణ అవసరం?', defaultQuestion: 'అగ్ర {service} సదుపాయాలను చూపించి సాక్ష్యాన్ని వివరించండి.', fallbackAnswer: 'ర్యాంకింగ్‌లు సాక్ష్య ఫీల్డ్‌లు, మూలాలు, సంప్రదింపు సామర్థ్యం, స్థానం పూర్తి స్థాయి మరియు మానవ ధృవీకరణను కలుపుతాయి.',
    trustReviewActions: 'నమ్మకం సమీక్ష చర్యలు', datedInfo: 'ఇక్కడ చూపిన సమాచారం తేదీతో ఉంటుంది. తదుపరి వినియోగదారు చూడే సమాచారాన్ని తాజా చేయడానికి మూలాలను ధృవీకరించండి, ఏజెంట్ బ్రిక్స్ సమీక్ష లేదా సదుపాయం కాల్ ఉపయోగించండి.', callFacilityDemo: 'సదుపాయానికి కాల్ చేయండి (డెమో)', calling: 'కాల్ చేస్తోంది…', serviceAvailable: 'సేవ ప్రస్తుతం అందుబాటులో ఉంది', equipmentConfirmed: 'పరికరాలు/సదుపాయాలు ధృవీకరించబడ్డాయి', specialistsConfirmed: 'నిపుణులు/రెఫరల్ మార్గం ధృవీకరించబడింది', reviewStatus: 'సమీక్ష స్థితి:', addNotePlaceholder: 'నోట్ జోడించండి, ఉదా. ఈ సదుపాయానికి NICU ధృవీకరణ అవసరం', submitReview: 'సమీక్ష సమర్పించండి', reviewSubmitted: 'సమీక్ష సమర్పించబడింది.', overrideScorePlaceholder: 'స్కోర్ % మార్చండి, ప్రస్తుతం {score}', saveScoreOverride: 'స్కోర్ ఓవర్‌రైడ్ సేవ్ చేయండి', reasonOverride: 'స్కోర్ ఓవర్‌రైడ్ కారణం', scoreOverrideSaved: 'స్కోర్ ఓవర్‌రైడ్ సేవ్ చేయబడింది.', scenarioPlaceholder: 'సన్నివేశం, ఉదా. {location}లో {service} ఎంపికలు', saveScenarios: 'సన్నివేశాలను సేవ్ చేయండి', scenarioSaved: 'సన్నివేశం సేవ్ చేయబడింది.',
    latestFacilityInfo: 'తాజా సదుపాయ సమాచారం', savedLakebaseInfo: 'Lakebaseలో సేవ్ చేయబడింది, కాబట్టి భవిష్యత్ వినియోగదారులు తాజా మూల తనిఖీలు, ఏజెంట్ సమీక్షలు, సమీక్షలు, ఓవర్‌రైడ్‌లు మరియు కాల్ నోట్స్ చూడగలరు.', noRecentUpdates: 'ఇంకా తాజా అప్‌డేట్లు లేవు. ఈ సదుపాయాన్ని తాజా చేయడానికి మూల ధృవీకరణ, ఏజెంట్ సమీక్ష లేదా సదుపాయం కాల్ ఉపయోగించండి.',
  },
};

function translate(language, key, values = {}) {
  const template = I18N[language]?.[key] || I18N.en[key] || key;
  return Object.entries(values).reduce((text, [name, value]) => text.replaceAll(`{${name}}`, value ?? ''), template);
}


const FACILITY_NAME_TRANSLATIONS = {
  'fallback-aravind-madurai': { hi: 'अरविंद नेत्र अस्पताल, मदुरै', te: 'అరవింద్ కంటి ఆసుపత్రి, మదురై' },
  'fallback-narayana-bengaluru': { hi: 'नारायण हृदय विज्ञान संस्थान, बेंगलुरु', te: 'నారాయణ హృదయ శాస్త్రాల సంస్థ, బెంగళూరు' },
  'fallback-fortis-delhi': { hi: 'फोर्टिस एस्कॉर्ट्स हार्ट इंस्टीट्यूट, नई दिल्ली', te: 'ఫోర్టిస్ ఎస్కార్ట్స్ హార్ట్ ఇన్‌స్టిట్యూట్, న్యూ ఢిల్లీ' },
  'aravind eye hospital, madurai': { hi: 'अरविंद नेत्र अस्पताल, मदुरै', te: 'అరవింద్ కంటి ఆసుపత్రి, మదురై' },
  'narayana institute of cardiac sciences': { hi: 'नारायण हृदय विज्ञान संस्थान, बेंगलुरु', te: 'నారాయణ హృదయ శాస్త్రాల సంస్థ, బెంగళూరు' },
  'fortis escorts heart institute': { hi: 'फोर्टिस एस्कॉर्ट्स हार्ट इंस्टीट्यूट, नई दिल्ली', te: 'ఫోర్టిస్ ఎస్కార్ట్స్ హార్ట్ ఇన్‌స్టిట్యూట్, న్యూ ఢిల్లీ' },
};

function canonicalFacilityName(value = '') {
  return String(value || '').toLowerCase().replace(/[^a-z0-9]+/g, ' ').replace(/\s+/g, ' ').trim();
}

function getFacilityDisplayName(facility = {}, language = 'en') {
  const baseName = facility.name || facility.facility_name || facility.facility_unique_id || facility.facility_id || facility.unique_id || '';
  if (!baseName) return '';
  if (language === 'en') return baseName;
  const direct = facility[`name_${language}`]
    || facility[`facility_name_${language}`]
    || facility.localized_names?.[language]
    || facility.translated_names?.[language]
    || facility.translations?.name?.[language]
    || facility.source_row?.[`name_${language}`]
    || facility.source_row?.[`facility_name_${language}`]
    || facility.source_row?.localized_names?.[language]
    || facility.source_row?.translated_names?.[language];
  if (direct) return direct;
  const idKey = facility.unique_id || facility.facility_unique_id || facility.facility_id;
  if (idKey && FACILITY_NAME_TRANSLATIONS[idKey]?.[language]) return FACILITY_NAME_TRANSLATIONS[idKey][language];
  const canonical = canonicalFacilityName(baseName);
  if (FACILITY_NAME_TRANSLATIONS[canonical]?.[language]) return FACILITY_NAME_TRANSLATIONS[canonical][language];
  const partialKey = Object.keys(FACILITY_NAME_TRANSLATIONS).find((key) => canonical && (canonical.includes(key) || key.includes(canonical)));
  return partialKey && FACILITY_NAME_TRANSLATIONS[partialKey]?.[language] ? FACILITY_NAME_TRANSLATIONS[partialKey][language] : baseName;
}

const fallbackFacilities = [
  { unique_id: 'fallback-aravind-madurai', name: 'Aravind Eye Hospital, Madurai', country: 'India', state: 'Tamil Nadu', city: 'Madurai', pincode: '625020', latitude: 9.9252, longitude: 78.1198, score: 8.5, confidence_label: 'High', specialties: ['Ophthalmology'], evidence_summary: 'Cataract, retina, glaucoma and ophthalmic equipment evidence appears in source fields.', source_urls: ['https://aravind.org/hospitals/madurai/'], uncertainty_flags: ['Verify live procedure availability before referral.'] },
  { unique_id: 'fallback-narayana-bengaluru', name: 'Narayana Institute of Cardiac Sciences', country: 'India', state: 'Karnataka', city: 'Bengaluru', pincode: '560099', latitude: 12.811, longitude: 77.6948, score: 8.2, confidence_label: 'High', specialties: ['Cardiology / CTVS'], evidence_summary: 'Cardiac surgery, cath lab, cardiac ICU and coronary intervention evidence found.', source_urls: ['https://www.narayanahealth.org'], uncertainty_flags: ['Human verification recommended for current surgical capacity.'] },
  { unique_id: 'fallback-fortis-delhi', name: 'Fortis Escorts Heart Institute', country: 'India', state: 'Delhi', city: 'New Delhi', pincode: '110025', latitude: 28.5613, longitude: 77.2749, score: 7.8, confidence_label: 'Medium', specialties: ['Cardiology / CTVS'], evidence_summary: 'Heart institute with cardiac surgery and critical care source evidence.', source_urls: ['https://www.fortishealthcare.com'], uncertainty_flags: ['Confirm procedure-specific eligibility and referral pathway.'] },
];

const api = async (path, options) => {
  const res = await fetch(path, { headers: { 'content-type': 'application/json' }, ...options });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json();
};

const fmt = (value) => Number(value || 0).toFixed(1);
const fmtPercent = (value) => {
  const n = Number(value || 0);
  return Number.isFinite(n) ? `${Math.round(n * 10)}%` : '0%';
};
const fmtCompactScore = (value) => {
  const n = Number(value || 0);
  return Number.isFinite(n) ? n.toFixed(2).replace(/\.?0+$/, '') : '0';
};

const TERM_LABELS = {
  internalMedicine: 'Internal medicine', generalSurgery: 'General surgery', orthopedicSurgery: 'Orthopedic surgery',
  physicalMedicineAndRehabilitation: 'Physical medicine & rehabilitation', oralAndMaxillofacialSurgery: 'Oral & maxillofacial surgery',
  critical: 'Critical care', criti: 'Critical care', ambulance: 'Ambulance service',
};

function humanizeTerm(value) {
  const raw = String(value || '').trim().replace(/^[\'"\[]+|[\'"\]]+$/g, '');
  if (!raw || raw === 'null' || raw === 'undefined') return '';
  if (TERM_LABELS[raw]) return TERM_LABELS[raw];
  const spaced = raw.replace(/([a-z])([A-Z])/g, '$1 $2').replace(/[_-]+/g, ' ')
    .replace(/\bctvs\b/ig, 'CTVS').replace(/\bicu\b/ig, 'ICU').replace(/\bcabg\b/ig, 'CABG').replace(/\boct\b/ig, 'OCT')
    .replace(/\s+/g, ' ').trim();
  return spaced.replace(/\b\w/g, (c) => c.toUpperCase()).replace(/\b(And|Or|Of)\b/g, (w) => w.toLowerCase());
}

function termList(values, limit = 6) {
  let items = Array.isArray(values) ? values : [];
  if (!items.length && typeof values === 'string') {
    try { const parsed = JSON.parse(values); items = Array.isArray(parsed) ? parsed : [values]; }
    catch (_) { items = values.split(/[,;|]+/); }
  }
  const seen = new Set();
  return items.map(humanizeTerm).filter((x) => x && !seen.has(x) && seen.add(x)).slice(0, limit);
}

function formatInfoDate(value) {
  if (!value) return 'No recent update yet';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value).slice(0, 16);
  return date.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' });
}
function actionInfoDate(action = {}) { return action.action_data?.information_date || action.updated_at || action.created_at; }
function latestInfoDate(actions = [], facility = {}) { return actionInfoDate(actions[0] || {}) || facility.last_updated || facility.source_row?.recency_of_page_update || ''; }

function EvidencePillGroup({ title, items, empty }) {
  return <div className="trustPillGroup"><h3>{title}</h3>{items.length ? <div className="trustPills">{items.map((item) => <span key={item}>{item}</span>)}</div> : <p>{empty}</p>}</div>;
}

function displayConfidence(f = {}) {
  if (f.human_verified || f.human_verification_status === 'verified') return 'Human verified';
  const score = Number(f.score || f.final_score || 0);
  if (score >= 8) return 'High';
  if (score >= 6) return 'Medium';
  return f.confidence_label || 'Needs review';
}

function classForConfidence(label = '') {
  const t = label.toLowerCase();
  if (t.includes('verified') || t.includes('high')) return 'hi';
  if (t.includes('medium')) return 'med';
  return 'low';
}

function normalizeFacility(f, rank = 0) {
  return { ...f, rank: f.rank || rank + 1, country: f.country || 'India', latitude: toNum(f.latitude), longitude: toNum(f.longitude), score: Number(f.score || f.final_score || 0) };
}
function toNum(v) { const n = Number(v); return Number.isFinite(n) ? n : null; }
const rad = (d) => d * Math.PI / 180;
function distanceKm(a, b) {
  if (![a?.latitude, a?.longitude, b?.latitude, b?.longitude].every((v) => Number.isFinite(Number(v)))) return null;
  const R = 6371, dLat = rad(b.latitude - a.latitude), dLon = rad(b.longitude - a.longitude);
  const lat1 = rad(a.latitude), lat2 = rad(b.latitude);
  const h = Math.sin(dLat/2)**2 + Math.cos(lat1)*Math.cos(lat2)*Math.sin(dLon/2)**2;
  return 2 * R * Math.asin(Math.sqrt(h));
}


function LanguageSelect({ language, setLanguage, tr }) {
  return <label className="languageSelect"><span>{tr('appLanguage')}</span><select aria-label={tr('appLanguage')} value={language} onChange={(e) => setLanguage(e.target.value)}>{LANGUAGES.map((item) => <option key={item.code} value={item.code}>{item.label}</option>)}</select></label>;
}

function AppHeader({ activeTab, setActiveTab, selected, language, setLanguage, tr }) {
  return <header className="topbar">
    <div className="brandNav">
      <div className="brandBlock"><img className="brandLogo" src="/static/caresignal-logo.jpg" alt="CareSignal logo" /><div className="brandText"><div className="brand">Care<span>Signal</span></div><div className="brandSub">{tr('brandSub')}</div></div></div>
      <nav className="tabs" aria-label={tr('mainSections')}>{TABS.map((tab) => <button key={tab.id} className={`${activeTab === tab.id ? 'active' : ''} ${tab.id === 'assistant' ? 'assistantTab' : ''}`.trim()} onClick={() => setActiveTab(tab.id)}>{tr(tab.labelKey)}</button>)}</nav>
    </div>
    <div className="callTop"><LanguageSelect language={language} setLanguage={setLanguage} tr={tr} /><b>Digital Call Assistant</b><a href={`tel:${PHONE_TEL}`} aria-label={tr('callAria', { phone: PHONE_DISPLAY })}>☎ {PHONE_DISPLAY}</a></div>
  </header>;
}

function ProcedureDropdown({ services, selectedValues, onChange, tr }) {
  const [open, setOpen] = useState(false);
  const selectedSet = new Set(selectedValues || []);
  const selectedLabels = services.filter((s) => selectedSet.has(s.service_id)).map((s) => humanizeTerm(s.service_label));
  const summary = selectedLabels.length === 0 ? tr('selectProcedures') : selectedLabels.length === 1 ? selectedLabels[0] : tr('proceduresSelected', { count: selectedLabels.length });
  const toggle = (id) => {
    const next = selectedSet.has(id) ? selectedValues.filter((value) => value !== id) : [...selectedValues, id];
    onChange(next.length ? next : [services[0]?.service_id].filter(Boolean));
  };
  return <div className="procedureDropdown"><button type="button" className="procedureToggle" onClick={() => setOpen((x) => !x)} aria-expanded={open}>{summary}</button>{open && <div className="procedureMenu">{services.map((s) => <label key={s.service_id} className="procedureOption"><input type="checkbox" checked={selectedSet.has(s.service_id)} onChange={() => toggle(s.service_id)} /> <span>{humanizeTerm(s.service_label)}</span></label>)}</div>}</div>;
}

function FilterBar({ filters, values, setters, services, tr }) {
  const opts = (items, allLabel) => [{ value: '', label: allLabel }, ...(items || [])];
  const citiesForState = values.state && Array.isArray(filters.state_cities)
    ? Array.from(new Set(filters.state_cities.filter((row) => row.state === values.state).map((row) => row.city).filter(Boolean))).sort().map((city) => ({ value: city, label: city }))
    : filters.cities;
  return <section className="filterCard">
    <label><span>{tr('country')}</span><select value={values.country} onChange={(e) => setters.setCountry(e.target.value)}>{opts(filters.countries, tr('allCountries')).map((o) => <option key={o.value || o.label} value={o.value}>{o.label}</option>)}</select></label>
    <label><span>{tr('stateRegion')}</span><select value={values.state} onChange={(e) => { setters.setState(e.target.value); setters.setCity(''); setters.setPincode(''); }}>{opts(filters.states, tr('allStates')).map((o) => <option key={o.value || o.label} value={o.value}>{o.label}</option>)}</select></label>
    <label><span>{tr('city')}</span><select value={values.city} onChange={(e) => { setters.setCity(e.target.value); setters.setPincode(''); }}>{opts(citiesForState, values.state ? tr('allCitiesInState') : tr('allCities')).map((o) => <option key={o.value || o.label} value={o.value}>{o.label}</option>)}</select></label>
    <label><span>{tr('postalCode')}</span><select value={values.pincode} onChange={(e) => setters.setPincode(e.target.value)}>{opts(filters.pincodes, tr('allPostalCodes')).map((o) => <option key={o.value || o.label} value={o.value}>{o.label}</option>)}</select></label>
    <label><span>{tr('procedure')}</span><ProcedureDropdown services={services} selectedValues={values.services} onChange={setters.setServices} tr={tr} /></label>
    <label><span>{tr('radius')}</span><select value={values.radius} onChange={(e) => setters.setRadius(Number(e.target.value))}>{[25, 50, 100, 250, 500, 750, 751].map((km) => <option key={km} value={km}>{km > 750 ? '>750KM' : `${km} km`}</option>)}</select></label>
  </section>;
}

function FacilityTable({ facilities, selected, setSelected, onOpenTrust, onOpenReview, language, tr }) {
  const [rankFilter, setRankFilter] = useState('');
  const [nameFilter, setNameFilter] = useState('');
  const [locationFilter, setLocationFilter] = useState('');
  const [trustFilter, setTrustFilter] = useState('');
  const [confidenceValue, setConfidenceValue] = useState('');
  const choose = (f) => { setSelected(f); onOpenTrust(f); };
  const review = (f, e) => { e.stopPropagation(); setSelected(f); onOpenReview?.(f); };
  const baseRows = facilities.map((f, i) => ({ f, displayName: getFacilityDisplayName(f, language), rank: i + 1, confidence: Math.round(Number(f.score || 0) * 10), trustTier: f.source_row?.trust_tier || displayConfidence(f), location: [f.city, f.state, f.pincode].filter(Boolean).join(', ') }));
  const locationOptions = Array.from(new Set(baseRows.map((row) => row.location).filter(Boolean))).sort();
  const rows = baseRows.filter(({ f, displayName, rank, confidence, trustTier, location }) => (!rankFilter || String(rank).startsWith(rankFilter.trim())) && (!nameFilter || `${displayName} ${f.name || ''}`.toLowerCase().includes(nameFilter.trim().toLowerCase())) && (!locationFilter || location === locationFilter) && (!trustFilter || trustTier.toLowerCase().includes(trustFilter)) && (!confidenceValue || confidence >= Number(confidenceValue)));
  return <section className="card rankings"><div className="cardTitle"><h2>{tr('rankedFacilities')}</h2></div><table className="rank"><thead><tr><th>{tr('rank')}</th><th>{tr('facility')}</th><th>{tr('location')}</th><th>{tr('confidencePct')}</th><th>{tr('trustTier')}</th><th>{tr('evidence')}</th></tr><tr className="rankFilterRow"><th><input value={rankFilter} onChange={(e) => setRankFilter(e.target.value)} placeholder={tr('rank')} /></th><th><input value={nameFilter} onChange={(e) => setNameFilter(e.target.value)} placeholder={tr('facilityName')} /></th><th><select value={locationFilter} onChange={(e) => setLocationFilter(e.target.value)}><option value="">{tr('allLocations')}</option>{locationOptions.map((loc) => <option key={loc} value={loc}>{loc}</option>)}</select></th><th><input type="number" min="0" max="100" value={confidenceValue} onChange={(e) => setConfidenceValue(e.target.value)} placeholder={tr('confidence')} /></th><th><select value={trustFilter} onChange={(e) => setTrustFilter(e.target.value)}><option value="">{tr('all')}</option><option value="high">{tr('high')}</option><option value="medium">{tr('medium')}</option><option value="needs">{tr('needsReview')}</option><option value="verified">{tr('verified')}</option></select></th><th></th></tr></thead><tbody>{rows.map(({ f, displayName, rank, confidence, trustTier, location }) => <tr key={f.unique_id} className={selected?.unique_id === f.unique_id ? 'selected' : ''} onClick={() => choose(f)}><td>{rank}</td><td><span className="facilityName" title={f.name}>{displayName}</span></td><td>{location}</td><td><b>{confidence}%</b></td><td><span className={`badge ${classForConfidence(displayConfidence(f))}`}>{trustTier}</span></td><td><button className="evidenceLink" onClick={(e) => review(f, e)}>{tr('clickHere')}</button></td></tr>)}</tbody></table>{!rows.length && <p className="empty">{tr('noFacilities')}</p>}</section>;
}

function normalizeUrlList(...values) {
  const urls = [];
  const add = (value) => {
    if (!value) return;
    if (Array.isArray(value)) { value.forEach(add); return; }
    if (typeof value === 'object') { Object.values(value).forEach(add); return; }
    String(value).split(/[\s,;|]+/).map((x) => x.trim()).filter(Boolean).forEach((item) => {
      const cleaned = item.replace(/^["'\[]+|["'\]]+$/g, '');
      if (/^https?:\/\//i.test(cleaned) && !urls.includes(cleaned)) urls.push(cleaned);
    });
  };
  values.forEach(add);
  return urls;
}

function scoreBreakdownEntries(facility, sources, specialties, procedures, equipment) {
  const parseRaw = (raw) => {
    if (!raw) return [];
    if (typeof raw === 'string') {
      try { return parseRaw(JSON.parse(raw)); }
      catch (_) { return []; }
    }
    if (Array.isArray(raw)) {
      return raw.map((x, i) => Array.isArray(x) ? x : [x.label || x.key || x.name || `Component ${i + 1}`, x.score ?? x.value ?? 0, x.max_score ?? x.max]);
    }
    if (typeof raw === 'object') return Object.entries(raw).map(([k, v]) => Array.isArray(v) ? [k, v[0], v[1]] : [k, v]);
    return [];
  };
  const rawEntries = parseRaw(facility.score_breakdown || facility.source_row?.score_breakdown || facility.scoring_breakdown);
  const usableRaw = rawEntries.filter(([k, v]) => k && v !== undefined && v !== null && v !== '');
  if (usableRaw.length) return usableRaw;
  const termCount = specialties.length + procedures.length + equipment.length;
  const locationParts = [facility.city, facility.state, facility.pincode, facility.country].filter(Boolean).length;
  const hasContact = Boolean(facility.phone || facility.phone_number || facility.contact_number || facility.website || facility.source_url || sources.length);
  const verified = facility.human_verified || facility.human_verification_status === 'verified' || String(facility.status || '').toLowerCase().includes('verified');
  return [
    ['Trust Score', fmtPercent(facility.score)],
    ['Evidence Match', `${Math.min(100, 45 + termCount * 10)}%`],
    ['Source Coverage', sources.length ? '100%' : '0%'],
    ['Contactability', hasContact ? '100%' : '50%'],
    ['Location Completeness', `${Math.round((locationParts / 4) * 100)}%`],
    ['Human Verification', verified ? '100%' : 'Pending'],
  ];
}

function formatBreakdownValue(value, max) {
  if (typeof value === 'string') return value;
  return `${fmtCompactScore(value)}${max ? `/${fmtCompactScore(max)}` : ''}`;
}

function SourceVerificationPanel({ verification }) {
  if (!verification) return null;
  const checks = verification.checks || [];
  const agent = verification.agent_bricks;
  return <div className="sourceVerifyPanel">
    <div><b>{humanizeTerm(verification.status || 'verification')}</b><span>{verification.summary}</span></div>
    <div className="sourceVerifyStats"><span>{verification.verified_count || 0} Verified</span><span>{verification.partial_count || 0} Partial</span><span>{verification.failed_count || 0} Failed</span></div>
    {agent && <p className={`agentBrickNote ${agent.status === 'ok' ? 'ok' : ''}`}><b>Agent Bricks:</b> {agent.summary}</p>}
    {checks.slice(0, 3).map((check) => <div className="sourceCheck" key={check.url}>
      <span className={`badge ${classForConfidence(check.status)}`}>{humanizeTerm(check.status)}</span>
      <a href={check.url} target="_blank" rel="noreferrer">{check.url}</a>
      {check.excerpt && <small>{check.excerpt}</small>}
    </div>)}
  </div>;
}

function TrustCard({ facility, serviceLabel, onClose, onMethodology, verification, verifying, onVerifySources, language, tr }) {
  if (!facility) return null;
  const sources = normalizeUrlList(facility.source_urls, facility.source_url, facility.website, facility.source_row?.source_urls, facility.source_row?.websites);
  const specialties = termList(facility.specialties, 12);
  const procedures = termList(facility.procedures, 12);
  const equipment = termList(facility.equipment, 8);
  const entries = scoreBreakdownEntries(facility, sources, specialties, procedures, equipment);
  const currentVerification = verification?.facility_id === facility.unique_id ? verification : null;
  const displayName = getFacilityDisplayName(facility, language);
  return <div className="trustModal" role="dialog" aria-modal="true" aria-label={`${tr('trustCard')} for ${displayName}`} onClick={onClose}><aside className="card trust trustSheet" onClick={(e) => e.stopPropagation()}><button className="trustClose" aria-label="Close Trust Card" onClick={onClose}>×</button><div className="trustHero"><div><span className="eyebrow">{tr('trustCard')}</span><h2 title={facility.name}>{displayName}</h2><p>{[facility.city, facility.state, facility.pincode].filter(Boolean).join(', ') || tr('locationPending')}</p></div><div className="scoreBubble"><b>{fmtPercent(facility.score)}</b><span>{tr('trustScore')}</span></div></div><div className="trustClaim"><span className={`badge ${classForConfidence(displayConfidence(facility))}`}>{displayConfidence(facility)}</span><p><b>{tr('claim')}</b> {tr('supports', { service: serviceLabel })}</p><button className="methodLink" onClick={onMethodology}>{tr('howScoreWorks')}</button></div><div className="trustAgentActions"><button onClick={() => onVerifySources?.('crawl')} disabled={verifying || !sources.length}>{verifying ? tr('verifying') : tr('verifySourceLinks')}</button><button onClick={() => onVerifySources?.('agent')} disabled={verifying || !sources.length}>{tr('agentBricksReview')}</button></div><SourceVerificationPanel verification={currentVerification} /><div className="trustSection trustEvidenceLead"><EvidencePillGroup title={tr('specialties')} items={specialties} empty={tr('noSpecialties')} /><EvidencePillGroup title={tr('procedures')} items={procedures} empty={tr('noProcedures')} />{equipment.length > 0 && <EvidencePillGroup title={tr('equipmentServices')} items={equipment} empty="" />}{facility.description && <p className="trustDescription">{facility.description.slice(0, 240)}</p>}</div><div className="trustSection"><h3>{tr('scoreBreakdown')}</h3><div className="why">{entries.slice(0, 8).map(([k, v, m]) => <div key={k}><b>{formatBreakdownValue(v, m)}</b><span>{humanizeTerm(k)}</span></div>)}</div></div><div className="sources trustSection"><h3>{tr('sources')}</h3>{sources.slice(0, 3).map((url) => <a key={url} href={url} target="_blank" rel="noreferrer">{url}</a>)}{!sources.length && <span>{tr('noSourceUrl')}</span>}</div><p className="footer"><b>{tr('uncertainty')}</b> {(facility.uncertainty_flags || [tr('defaultUncertainty')]).join('; ')}</p></aside></div>;
}

function MethodologyModal({ onClose }) {
  return <div className="trustModal" role="dialog" aria-modal="true" aria-label="CareSignal score methodology" onClick={onClose}><aside className="card methodologySheet" onClick={(e) => e.stopPropagation()}><button className="trustClose" aria-label="Close methodology" onClick={onClose}>×</button><span className="eyebrow dark">Scoring Methodology</span><h2>How CareSignal Ranks Facilities</h2><ul><li><b>Evidence match:</b> specialties, procedures, equipment, capabilities, and descriptions are matched to the selected service.</li><li><b>Operational readiness:</b> phone/website contactability and location completeness improve trust.</li><li><b>Human verification:</b> verified claims get a boost; rejected or uncertain claims are penalized.</li><li><b>Uncertainty penalties:</b> sparse evidence, missing source URLs, or missing contact paths are surfaced for follow-up.</li></ul><p>This is a planning aid, not medical advice. Referral decisions should still be confirmed directly with the facility.</p></aside></div>;
}

function googleMapZoom(radius) { return radius <= 50 ? 10 : radius <= 150 ? 8 : radius <= 350 ? 7 : 6; }
function googleEmbedSrc(center, radius) {
  const lat = Number(center?.latitude), lng = Number(center?.longitude);
  if (!Number.isFinite(lat) || !Number.isFinite(lng)) return '';
  return `https://maps.google.com/maps?ll=${encodeURIComponent(`${lat},${lng}`)}&q=${encodeURIComponent(`${lat},${lng}`)}&z=${googleMapZoom(radius)}&t=m&output=embed`;
}
function GoogleMapView({ center, radius, language, tr }) {
  const embedSrc = googleEmbedSrc(center, radius);
  if (!embedSrc) return <div className="googleMapWrap"><div className="mapOverlay"><b>{tr('googleMapsUnavailable')}</b><span>{tr('selectFacilityMap')}</span></div></div>;
  return <div className="googleMapWrap"><iframe title={`Google map for ${getFacilityDisplayName(center, language) || 'selected facility'}`} className="googleMapFrame" src={embedSrc} loading="lazy" referrerPolicy="no-referrer-when-downgrade" /></div>;
}
function RadiusMap({ facilities, selected, setSelected, radius, setRadius, onOpenTrust, language, tr }) {
  const center = selected || facilities[0];
  const effectiveRadius = Number(radius) > 750 ? Infinity : Number(radius);
  const visible = useMemo(() => facilities.map((f) => ({ facility: f, distance: distanceKm(center, f) })).filter(({ facility, distance }) => distance === null || distance <= effectiveRadius || facility.unique_id === center?.unique_id), [facilities, center?.unique_id, center?.latitude, center?.longitude, effectiveRadius]);
  return <section className="card mapCard"><div className="cardTitle"><h2>{tr('googleMapsRadius')}</h2><span>{tr('insideRadius', { count: visible.length })}</span></div><div className="radiusControl"><label>{tr('radius')}: <b>{Number(radius) > 750 ? '>750KM' : `${radius} km`}</b><input type="range" min="25" max="751" step="25" value={radius} onChange={(e) => setRadius(Number(e.target.value))} /></label></div><GoogleMapView center={center} radius={radius} language={language} tr={tr} /><div className="mapList">{visible.slice(0, 8).map(({ facility: f, distance }) => <button key={f.unique_id} onClick={() => { setSelected(f); onOpenTrust(f); }}><b title={f.name}>{getFacilityDisplayName(f, language)}</b><span>{distance?.toFixed(0) || 0} km • {f.city || f.state} • {tr('viewTrustCard')}</span></button>)}</div></section>;
}
function buildDemoCallPreview(facility, procedure, serviceLabel, displayName) {
  const name = displayName || facility?.name || 'Selected Facility';
  const lower = name.toLowerCase();
  const cardiacTurns = [
    ['CareSignal Agent', `Hello, I am calling on behalf of a care coordinator. Can you confirm whether ${name} currently handles ${serviceLabel} referrals?`],
    ['Facility Desk', 'Yes, cardiac cases are handled through our cardiac sciences team. Please route patient reports and urgency details to the coordinator.'],
    ['CareSignal Agent', 'Is ICU or post-operative critical care coordination available if the case is accepted?'],
    ['Facility Desk', 'Yes, but bed status changes during the day. The coordinator must confirm availability before transfer.'],
    ['CareSignal Agent', 'What should the referring team prepare before calling back?'],
    ['Facility Desk', 'Diagnosis, recent reports, patient vitals, insurance or payment details, and expected arrival time.'],
  ];
  const genericTurns = [
    ['CareSignal Agent', `Hello, I am checking whether ${name} can handle a referral for ${serviceLabel}.`],
    ['Facility Desk', 'We can route the inquiry, but the department coordinator needs patient details before confirming.'],
    ['CareSignal Agent', 'What information should the care coordinator prepare?'],
    ['Facility Desk', 'Diagnosis, recent reports, current condition, payer details, and requested appointment or transfer date.'],
  ];
  const conversation = (lower.includes('narayana') || lower.includes('cardiac') || lower.includes('fortis') || lower.includes('escorts') ? cardiacTurns : genericTurns).map(([speaker, line]) => ({ speaker, text: line }));
  return {
    facility_id: facility?.unique_id,
    facility_name: name,
    procedure,
    service_label: serviceLabel,
    status: 'playing_demo_call',
    information_date: new Date().toISOString(),
    summary: `Playing demo call with ${name}. Final notes will be saved to Lakebase after this simulated facility call completes.`,
    verified_claims: ['Demo call playback started from the Call Facility button.', 'Transcript is shown turn-by-turn for the live demo.'],
    open_questions: ['Real call-agent integration is still pending.'],
    recommendation: 'Use this playback for the demo, then use the saved call notes as dated facility information.',
    conversation,
    playback_seed: Date.now(),
  };
}

function playDemoCallTone(kind = 'dial') {
  if (typeof window === 'undefined') return false;
  try {
    const Ctx = window.AudioContext || window.webkitAudioContext;
    if (!Ctx) return false;
    const ctx = window.__careSignalAudioContext || new Ctx();
    window.__careSignalAudioContext = ctx;
    if (ctx.state === 'suspended') ctx.resume();
    const now = ctx.currentTime;
    const make = (frequency, start, duration, gainValue = 0.045) => {
      const oscillator = ctx.createOscillator();
      const gain = ctx.createGain();
      oscillator.type = 'sine';
      oscillator.frequency.value = frequency;
      gain.gain.setValueAtTime(0.0001, now + start);
      gain.gain.exponentialRampToValueAtTime(gainValue, now + start + 0.02);
      gain.gain.exponentialRampToValueAtTime(0.0001, now + start + duration);
      oscillator.connect(gain).connect(ctx.destination);
      oscillator.start(now + start);
      oscillator.stop(now + start + duration + 0.03);
    };
    if (kind === 'agent') { make(720, 0, 0.16); make(920, 0.18, 0.12); }
    else if (kind === 'desk') { make(420, 0, 0.18); make(520, 0.2, 0.14); }
    else { make(350, 0, 0.22); make(440, 0.28, 0.22); make(350, 0.56, 0.22); }
    return true;
  } catch (_) {
    return false;
  }
}

function RecentHistory({ title, items, empty, language, tr }) {
  return <section className="card historyCard"><div className="cardTitle"><h2>{title}</h2><span>{tr('readBackLakebase')}</span></div><div className="historyList">{items.slice(0, 6).map((item) => { const data = item.action_data || {}; const label = item.action_type || item.status || item.verification_status || item.procedure || item.service; const detail = data.note || data.justification || data.notes || data.title || data.status || item.notes || item.location || 'Saved'; return <div key={item.action_id || item.verification_id || item.shortlist_id || item.created_at} className="historyItem"><b>{getFacilityDisplayName({ unique_id: item.facility_unique_id || item.facility_id || item.unique_id, name: item.facility_name || item.title || item.location }, language) || 'Scenario'}</b><span>{humanizeTerm(label)} • {detail}</span><small>{item.created_at || ''}</small></div>; })}{!items.length && <p className="empty">{empty}</p>}</div></section>;
}

function VerificationForm({ facility, service, serviceLabel, facilities, location, onVerified, onHistory, verification, verifying, onVerifySources, callResult, callingFacility, onCallFacility, language, tr }) {
  const status = 'verified';
  const [notes, setNotes] = useState('Verified by phone or visit.');
  const [overrideScore, setOverrideScore] = useState('');
  const [overrideReason, setOverrideReason] = useState('Local contact confirmed service capacity.');
  const [scenarioTitle, setScenarioTitle] = useState('');
  const [submitMessage, setSubmitMessage] = useState('');
  const [overrideMessage, setOverrideMessage] = useState('');
  const [scenarioMessage, setScenarioMessage] = useState('');
  if (!facility) return null;
  const currentVerification = verification?.facility_id === facility.unique_id ? verification : null;
  const displayName = getFacilityDisplayName(facility, language);
  const saveAction = async (action_type, action_data = {}) => {
    await api('/api/actions', { method: 'POST', body: JSON.stringify({ user_id: 'CareSignal demo user', facility_id: facility.unique_id, action_type, action_data: { procedure: service, facility_name: facility.name, ...action_data } }) });
    await onHistory?.();
  };
  const submit = async () => {
    setSubmitMessage('');
    const payload = { unique_id: facility.unique_id, procedure: service, status, verifier_name: 'CareSignal demo user', notes };
    try { const result = await api('/api/verifications', { method: 'POST', body: JSON.stringify(payload) }); onVerified(status, result.facility); }
    catch (_) { onVerified(status); }
    setSubmitMessage(tr('reviewSubmitted'));
    await onHistory?.();
  };
  const saveOverride = async () => {
    setOverrideMessage('');
    const oldScore = Number(facility.score || 0);
    const rawScore = Number(overrideScore || oldScore);
    const newScore = rawScore > 10 ? rawScore / 10 : rawScore;
    await saveAction('override', { old_score: oldScore, new_score: newScore, justification: overrideReason });
    setOverrideMessage(tr('scoreOverrideSaved'));
  };
  const saveScenario = async () => {
    setScenarioMessage('');
    const ids = (facilities || []).slice(0, 8).map((f) => f.unique_id);
    await api('/api/scenario-shortlists', { method: 'POST', body: JSON.stringify({ user_id: 'CareSignal demo user', location, service, facility_ids: ids, title: scenarioTitle || `${serviceLabel} options in ${location || 'India'}`, notes }) });
    await onHistory?.();
    setScenarioMessage(tr('scenarioSaved'));
  };
  return <section className="card verification trustReviewActions">
    <div className="cardTitle"><h2>{tr('trustReviewActions')}</h2></div>
    <p>{tr('datedInfo')}</p>
    <div className="trustAgentActions reviewActions"><button onClick={() => onVerifySources?.('crawl')} disabled={verifying}>{verifying ? tr('verifying') : tr('verifySourceLinks')}</button><button onClick={() => onVerifySources?.('agent')} disabled={verifying}>{tr('agentBricksReview')}</button><button onClick={() => onCallFacility?.()} disabled={callingFacility}>{callingFacility ? tr('calling') : tr('callFacilityDemo')}</button></div>
    <SourceVerificationPanel verification={currentVerification} />
    <CallNotesPanel result={callResult?.facility_id === facility.unique_id ? callResult : null} />
    <div className="checklist"><label><input type="checkbox" /> {tr('serviceAvailable')}</label><label><input type="checkbox" /> {tr('equipmentConfirmed')}</label><label><input type="checkbox" /> {tr('specialistsConfirmed')}</label></div>
    <p className="reviewStatusLine"><b>{tr('reviewStatus')}</b> {tr('verified')}</p>
    <textarea value={notes} onChange={(e) => setNotes(e.target.value)} placeholder={tr('addNotePlaceholder')} />
    <div className="assistantActions reviewSubmitRow"><button onClick={submit}>{tr('submitReview')}</button></div>
    {submitMessage && <p className="successMessage">{submitMessage}</p>}
    <div className="inlineActionGroup scoreOverrideGroup"><input value={overrideScore} onChange={(e) => setOverrideScore(e.target.value)} placeholder={tr('overrideScorePlaceholder', { score: fmtPercent(facility.score) })} /><button onClick={saveOverride}>{tr('saveScoreOverride')}</button></div>
    <textarea className="overrideReasonBox" value={overrideReason} onChange={(e) => setOverrideReason(e.target.value)} placeholder={tr('reasonOverride')} />
    {overrideMessage && <p className="successMessage compactSuccess">{overrideMessage}</p>}
    <div className="inlineActionGroup scenarioGroup"><input value={scenarioTitle} onChange={(e) => setScenarioTitle(e.target.value)} placeholder={tr('scenarioPlaceholder', { service: serviceLabel, location: location || 'India' })} /><button onClick={saveScenario}>{tr('saveScenarios')}</button></div>
    {scenarioMessage && <p className="successMessage compactSuccess">{scenarioMessage}</p>}
  </section>;
}

function CallNotesPanel({ result }) {
  const [playing, setPlaying] = useState(false);
  const [activeTurn, setActiveTurn] = useState(-1);
  const [audioStatus, setAudioStatus] = useState('Visual playback ready');
  const previousSeedRef = useRef(null);
  const playbackTimerRef = useRef(null);
  const playbackRunRef = useRef(0);
  const conversation = result?.conversation || [];
  const clearPlaybackTimer = () => {
    if (playbackTimerRef.current) {
      window.clearTimeout(playbackTimerRef.current);
      playbackTimerRef.current = null;
    }
  };
  const stopSpeech = () => {
    if (typeof window !== 'undefined' && window.speechSynthesis) window.speechSynthesis.cancel();
  };
  const estimateTurnMs = (turn) => {
    const text = `${turn?.speaker || ''}. ${turn?.text || ''}`;
    const wordCount = text.trim().split(/\s+/).filter(Boolean).length;
    return Math.max(3600, Math.min(12000, wordCount * 430 + 1200));
  };
  const advanceTurn = (index, runId) => {
    if (runId !== playbackRunRef.current) return;
    if (index >= conversation.length - 1) {
      setPlaying(false);
      setAudioStatus('Demo call playback complete');
      return;
    }
    const next = index + 1;
    setActiveTurn(next);
    speakTurn(next, runId);
  };
  const speakTurn = (index, runId = playbackRunRef.current) => {
    const turn = conversation[index];
    if (!turn || runId !== playbackRunRef.current) return;
    clearPlaybackTimer();
    const toneOk = playDemoCallTone(turn.speaker?.toLowerCase().includes('agent') ? 'agent' : 'desk');
    const fallbackMs = estimateTurnMs(turn);
    let finished = false;
    const finish = () => {
      if (finished) return;
      finished = true;
      clearPlaybackTimer();
      playbackTimerRef.current = window.setTimeout(() => advanceTurn(index, runId), 550);
    };
    if (typeof window !== 'undefined' && window.speechSynthesis) {
      try {
        const utterance = new SpeechSynthesisUtterance(`${turn.speaker}. ${turn.text}`);
        utterance.rate = 0.82;
        utterance.pitch = turn.speaker?.toLowerCase().includes('agent') ? 1.03 : 0.9;
        utterance.onstart = () => setAudioStatus('Voice playback active — completing each sentence');
        utterance.onend = finish;
        utterance.onerror = () => {
          setAudioStatus(toneOk ? 'Browser voice blocked; using timed transcript playback' : 'Audio blocked; transcript playback active');
          finish();
        };
        window.speechSynthesis.speak(utterance);
        playbackTimerRef.current = window.setTimeout(() => {
          if (!finished) {
            setAudioStatus(toneOk ? 'Timed transcript playback active' : 'Transcript playback active');
            finish();
          }
        }, fallbackMs);
      } catch (_) {
        setAudioStatus(toneOk ? 'Demo tones + transcript active' : 'Transcript playback active');
        playbackTimerRef.current = window.setTimeout(() => advanceTurn(index, runId), fallbackMs);
      }
    } else {
      setAudioStatus(toneOk ? 'Demo tones + transcript active' : 'Transcript playback active');
      playbackTimerRef.current = window.setTimeout(() => advanceTurn(index, runId), fallbackMs);
    }
  };
  const startPlayback = () => {
    if (!conversation.length) return;
    playbackRunRef.current += 1;
    const runId = playbackRunRef.current;
    clearPlaybackTimer();
    stopSpeech();
    playDemoCallTone('dial');
    setActiveTurn(0);
    setPlaying(true);
    setAudioStatus('Starting demo call playback');
    playbackTimerRef.current = window.setTimeout(() => speakTurn(0, runId), 250);
  };
  const stopPlayback = () => {
    playbackRunRef.current += 1;
    clearPlaybackTimer();
    setPlaying(false);
    setAudioStatus('Playback stopped');
    stopSpeech();
  };
  useEffect(() => {
    const seed = result?.playback_seed || result?.information_date || result?.summary;
    if (!result || !seed) return undefined;
    if (previousSeedRef.current !== seed) {
      previousSeedRef.current = seed;
      setActiveTurn(-1);
      setPlaying(false);
      setAudioStatus('Dialing facility…');
      const timer = window.setTimeout(startPlayback, 120);
      return () => window.clearTimeout(timer);
    }
    return undefined;
  }, [result?.playback_seed, result?.information_date]);
  useEffect(() => () => { clearPlaybackTimer(); stopSpeech(); playbackRunRef.current += 1; }, []);
  if (!result) return null;
  return <div className="callNotesPanel"><div><b>Live Demo Call</b><span>Information As Of {formatInfoDate(result.information_date)}</span></div><div className={`callPlaybackBar ${playing ? 'isPlaying' : ''}`} aria-live="polite"><span>{playing ? `▶ Playing Demo Call · Turn ${activeTurn + 1}/${conversation.length}` : audioStatus}</span><button type="button" onClick={playing ? stopPlayback : startPlayback}>{playing ? 'Stop Playback' : 'Play Demo Call'}</button></div><p>{result.summary}</p><div className="callNotesColumns"><div><h3>Confirmed</h3>{(result.verified_claims || []).map((item) => <span key={item}>{item}</span>)}</div><div><h3>Still Check</h3>{(result.open_questions || []).map((item) => <span key={item}>{item}</span>)}</div></div><div className="callTranscript"><h3>Demo Conversation</h3>{conversation.map((turn, i) => <p key={`${turn.speaker}-${i}`} className={i === activeTurn ? 'activeTurn' : i < activeTurn ? 'playedTurn' : ''}><b>{turn.speaker}:</b> {turn.text}</p>)}</div></div>;
}

function FacilityInfoTimeline({ actions, facility, tr }) {
  const rows = (actions || []).filter((action) => ['source_verification', 'call_note', 'review', 'override'].includes(action.action_type));
  return <section className="card infoTimeline"><div className="cardTitle"><h2>{tr('latestFacilityInfo')}</h2><span>As Of {formatInfoDate(latestInfoDate(rows, facility))}</span></div><p>{tr('savedLakebaseInfo')}</p><div className="infoTimelineList">{rows.slice(0, 6).map((action) => { const data = action.action_data || {}; const title = action.action_type === 'call_note' ? 'Call Notes' : data.mode === 'agent' ? tr('agentBricksReview') : action.action_type === 'source_verification' ? 'Verified Sources' : humanizeTerm(action.action_type); const detail = data.summary || data.notes || data.justification || data.status || 'Saved update'; return <div key={action.action_id || `${action.action_type}-${action.created_at}`} className="infoTimelineItem"><b>{title}</b><small>Information As Of {formatInfoDate(data.information_date || action.updated_at || action.created_at)}</small><span>{detail}</span>{Array.isArray(data.verified_claims) && data.verified_claims.length > 0 && <em>{data.verified_claims.slice(0, 2).join(' • ')}</em>}</div>; })}{!rows.length && <p className="empty">{tr('noRecentUpdates')}</p>}</div></section>;
}

function SelectedFacilityPanel({ selected, onOpenTrust, onAddShortlist, onViewShortlists, shortlistCount, userActionsCount, scenarioCount, latestDate, language, tr }) {
  return <section className="card selectedFacilityPanel">
    <div className="cardTitle"><h2>{tr('selectedFacility')}</h2></div>
    <p className="infoDateLine"><b>{tr('informationAsOf')}</b> {formatInfoDate(latestDate)}</p>
    {selected ? <div className="selectedFacilitySummary"><b title={selected.name}>{getFacilityDisplayName(selected, language)}</b><span>{[selected.city, selected.state, selected.pincode].filter(Boolean).join(', ')}</span><small>Score {fmtPercent(selected.score)} • {selected.trust_tier || selected.status || tr('reviewReady')}</small></div> : <p className="empty">{tr('selectFacilityToReview')}</p>}
    <div className="trustReviewButtonRow"><button className="trustOpenWide" onClick={() => onOpenTrust()} disabled={!selected}>{tr('openTrustCard')}</button><button className="trustOpenWide shortlistInline" onClick={onAddShortlist} disabled={!selected}>{tr('addToShortlist')}</button><button className="trustOpenWide shortlistInline" onClick={onViewShortlists} disabled={!shortlistCount}>{tr('viewShortlist', { count: shortlistCount })}</button></div>
    <p className="empty">{tr('savedActions', { actions: userActionsCount, scenarios: scenarioCount })}</p>
  </section>;
}

function TrustReviewFacilityFilter({ selected, facilities, onSelectFacility, language, tr }) {
  return <section className="trustReviewFacilityFilter"><label className="facilitySelectLabel"><span>{tr('facility')}</span><select value={selected?.unique_id || ''} onChange={(e) => onSelectFacility(e.target.value)}><option value="">{tr('selectFacility')}</option>{facilities.map((f) => <option key={f.unique_id} value={f.unique_id}>{getFacilityDisplayName(f, language)}</option>)}</select></label></section>;
}

function AssistantPanel({ service, serviceLabel, selected, language, tr }) {
  const selectedDisplayName = getFacilityDisplayName(selected, language);
  const defaultQuestion = tr('defaultQuestion', { service: serviceLabel });
  const [question, setQuestion] = useState(defaultQuestion);
  const [answer, setAnswer] = useState(null);
  useEffect(() => {
    setQuestion(defaultQuestion);
    setAnswer(null);
  }, [defaultQuestion, language]);
  const quickPrompts = [tr('topFacilitiesPrompt', { service: serviceLabel }), tr('explainFacilityPrompt', { facility: selectedDisplayName || tr('selectedFacility') }), tr('claimsNeedVerificationPrompt')];
  const ask = async (prompt = question) => {
    setQuestion(prompt);
    try { setAnswer(await api('/api/assistant/query', { method: 'POST', body: JSON.stringify({ question: prompt, procedure: service, unique_id: selected?.unique_id, language }) })); }
    catch (_) { setAnswer({ answer: tr('fallbackAnswer'), data: [] }); }
  };
  return <section className="card chartAssistant"><div className="cardTitle"><h2>{tr('chatAssistantTitle')}</h2><span>{tr('safeQueryTemplates')}</span></div><div className="promptChips">{quickPrompts.map((prompt) => <button key={prompt} onClick={() => ask(prompt)}>{prompt}</button>)}</div><textarea value={question} onChange={(e) => setQuestion(e.target.value)} /><div className="assistantActions"><button onClick={() => ask()}>{tr('generateAnswer')}</button><a className="voiceCallBtn" href={`tel:${PHONE_TEL}`}>Call {PHONE_DISPLAY}</a></div>{answer && <div className="assistantAnswer"><p>{answer.answer}</p><div className="bars">{(answer.data || []).slice(0, 6).map((row, i) => <div key={row.facility || row.name || i}><span>{row.facility || row.name || row.state}</span><i style={{ width: `${Math.min(100, (row.score || row.average_score || 5) * 10)}%` }} /></div>)}</div></div>}</section>;
}

function Shortlists({ selected, shortlists, onAdd, language }) {
  return <section className="card"><div className="cardTitle"><h2>Shortlists</h2><span>Planner Decisions</span></div><button onClick={onAdd} disabled={!selected}>Add Selected Facility</button><div className="shortlistItems">{shortlists.map((x) => <div key={x.id || x.shortlist_id} className="shortlistItem"><b>{getFacilityDisplayName({ unique_id: x.facility_unique_id || x.facility_id || x.unique_id, name: x.name || x.facility_name || x.facility_unique_id }, language)}</b><small>{x.meta || `${humanizeTerm(x.procedure)} • ${x.notes || 'Shortlisted'}`}</small></div>)}{!shortlists.length && <p className="empty">No Shortlisted Facilities Yet.</p>}</div></section>;
}
function ServiceTable({ services }) { return <section className="card"><div className="cardTitle"><h2>Services Grouped By Specialty</h2><span>Derived Table Preview</span></div><table className="rank"><thead><tr><th>Procedure</th><th>Specialty Group</th><th>Keywords</th></tr></thead><tbody>{services.map((s) => <tr key={s.service_id}><td>{s.service_label}</td><td>{s.specialty_group}</td><td><small>{s.keywords}</small></td></tr>)}</tbody></table></section>; }

function App() {
  const [activeTab, setActiveTab] = useState('explorer');
  const [language, setLanguage] = useState('en');
  const tr = useMemo(() => (key, values) => translate(language, key, values), [language]);
  const [filters, setFilters] = useState({ countries: [{ value: 'India', label: 'India' }], states: [], cities: [], pincodes: [], services: SERVICE_FALLBACK });
  const [country, setCountry] = useState('India'), [state, setState] = useState(''), [city, setCity] = useState(''), [pincode, setPincode] = useState(''), [selectedServices, setSelectedServices] = useState(['cardiac_surgery']);
  const [facilities, setFacilities] = useState(fallbackFacilities.map(normalizeFacility));
  const [selected, setSelected] = useState(normalizeFacility(fallbackFacilities[0]));
  const [trustOpen, setTrustOpen] = useState(false), [methodOpen, setMethodOpen] = useState(false);
  const [radius, setRadius] = useState(250);
  const [shortlists, setShortlists] = useState([]), [recentVerifications, setRecentVerifications] = useState([]);
  const [userActions, setUserActions] = useState([]), [scenarioShortlists, setScenarioShortlists] = useState([]);
  const [trustVerification, setTrustVerification] = useState(null), [trustVerifying, setTrustVerifying] = useState(false);
  const [facilityUpdates, setFacilityUpdates] = useState([]), [callResult, setCallResult] = useState(null), [callingFacility, setCallingFacility] = useState(false);
  const services = filters.services?.length ? filters.services : SERVICE_FALLBACK;
  const activeServices = selectedServices.length ? selectedServices : [services[0]?.service_id].filter(Boolean);
  const service = activeServices[0] || 'cardiac_surgery';
  const selectedServiceDefs = activeServices.map((id) => services.find((s) => s.service_id === id)).filter(Boolean);
  const serviceLabel = selectedServiceDefs.length > 1 ? selectedServiceDefs.map((s) => s.service_label).join(', ') : selectedServiceDefs[0]?.service_label || 'Selected Procedure';

  const refreshHistory = async () => {
    const [shortlistData, verificationData, actionData, scenarioData] = await Promise.allSettled([api('/api/shortlists/recent'), api('/api/verifications/recent'), api('/api/actions/recent'), api('/api/scenario-shortlists/recent')]);
    if (shortlistData.status === 'fulfilled') setShortlists(shortlistData.value.map((x) => ({ ...x, id: x.shortlist_id, name: x.facility_name })));
    if (verificationData.status === 'fulfilled') setRecentVerifications(verificationData.value);
    if (actionData.status === 'fulfilled') setUserActions(actionData.value);
    if (scenarioData.status === 'fulfilled') setScenarioShortlists(scenarioData.value);
  };
  const loadFacilityUpdates = async (facilityId = selected?.unique_id) => { if (!facilityId) { setFacilityUpdates([]); return; } try { setFacilityUpdates(await api(`/api/actions/recent?facility_id=${encodeURIComponent(facilityId)}&limit=20`)); } catch (_) { setFacilityUpdates([]); } };

  useEffect(() => { api(`/api/filters?ts=${Date.now()}`).then((data) => setFilters((old) => ({ ...old, ...data }))).catch(() => {}); refreshHistory(); }, []);
  useEffect(() => { loadFacilityUpdates(selected?.unique_id); }, [selected?.unique_id]);
  useEffect(() => { let mounted = true; const procedures = activeServices.length ? activeServices : ['cardiac_surgery']; const loadOne = (procedure) => { const params = new URLSearchParams({ procedure, limit: '100' }); if (country) params.set('country', country); if (state) params.set('state', state); if (city) params.set('city', city); if (pincode) params.set('pincode', pincode); return api(`/api/facilities/top?${params}`); }; Promise.allSettled(procedures.map(loadOne)).then((results) => { const merged = new Map(); results.forEach((result) => { if (result.status !== 'fulfilled') return; (Array.isArray(result.value) ? result.value : result.value.facilities || result.value.data || []).map(normalizeFacility).forEach((f) => { const old = merged.get(f.unique_id); if (!old || Number(f.score || 0) > Number(old.score || 0)) merged.set(f.unique_id, f); }); }); let rows = Array.from(merged.values()).sort((a, b) => b.score - a.score); if (!rows.length) rows = fallbackFacilities.map(normalizeFacility).filter((f) => (!country || f.country === country) && (!state || f.state === state) && (!city || f.city === city) && (!pincode || f.pincode === pincode)); if (mounted) { setFacilities(rows); setSelected(rows[0] || null); } }); return () => { mounted = false; }; }, [country, state, city, pincode, activeServices.join('|')]);
  useEffect(() => { const onKey = (e) => { if (e.key === 'Escape') { setTrustOpen(false); setMethodOpen(false); } }; window.addEventListener('keydown', onKey); return () => window.removeEventListener('keydown', onKey); }, []);

  const displayFacilities = facilities;
  const openTrust = (facility = selected) => { if (facility) { setSelected(facility); setTrustOpen(true); } };
  const openReview = (facility = selected) => { if (facility) setSelected(facility); setActiveTab('verification'); };
  const selectFacilityForReview = (uniqueId) => { const facility = displayFacilities.find((f) => f.unique_id === uniqueId); if (facility) { setSelected(facility); setTrustVerification(null); setCallResult(null); } };
  const onVerified = async (status, apiFacility) => { if (!selected) return; const delta = status === 'verified' ? 1.5 : status === 'rejected' ? -2 : 0.5; const updated = normalizeFacility(apiFacility || { ...selected, human_verification_status: status, human_verified: status === 'verified', score: Math.max(0, Math.min(10, Number(selected.score || 0) + delta)) }, 0); setSelected(updated); setFacilities((rows) => rows.map((f) => f.unique_id === updated.unique_id ? updated : f).sort((a, b) => b.score - a.score)); await refreshHistory(); };
  const addShortlist = async () => { if (!selected) return; const optimistic = { id: `${selected.unique_id}-${Date.now()}`, name: getFacilityDisplayName(selected, language), meta: `${serviceLabel} • ${selected.city || selected.state || 'India'}` }; setShortlists((x) => [optimistic, ...x]); try { await api('/api/shortlists', { method: 'POST', body: JSON.stringify({ unique_id: selected.unique_id, procedure: service, notes: `${serviceLabel} shortlist` }) }); await refreshHistory(); } catch (_) {} };
  const verifyTrustSources = async (mode = 'crawl') => { if (!selected) return; setTrustVerifying(true); setTrustVerification(null); try { const data = await api('/api/trust/verify-links', { method: 'POST', body: JSON.stringify({ unique_id: selected.unique_id, procedure: service, mode }) }); setTrustVerification(data.result); await refreshHistory(); await loadFacilityUpdates(selected.unique_id); } catch (err) { setTrustVerification({ facility_id: selected.unique_id, facility_name: selected.name, mode, status: 'error', summary: err.message || 'Source verification failed.', checks: [] }); } finally { setTrustVerifying(false); } };
  const callFacilityDemo = async () => { if (!selected) return; const preview = buildDemoCallPreview(selected, service, serviceLabel, getFacilityDisplayName(selected, language)); playDemoCallTone('dial'); setCallResult(preview); setCallingFacility(true); try { const data = await api('/api/trust/call-facility', { method: 'POST', body: JSON.stringify({ unique_id: selected.unique_id, procedure: service }) }); setCallResult({ ...data.result, playback_seed: Date.now() }); await refreshHistory(); await loadFacilityUpdates(selected.unique_id); } catch (err) { setCallResult({ ...preview, status: 'demo_call_error', summary: err.message || 'Demo call note generation failed; playing local demo transcript.' }); } finally { setCallingFacility(false); } };

  return <>
    <AppHeader activeTab={activeTab} setActiveTab={setActiveTab} selected={selected} language={language} setLanguage={setLanguage} tr={tr} />
    <main className="main">
      <section className="missionStrip">{tr('mission')}</section>
      {activeTab !== 'verification' && activeTab !== 'assistant' && <section className="hero filtersOnly"><FilterBar filters={filters} values={{ country, state, city, pincode, services: activeServices, radius }} setters={{ setCountry, setState, setCity, setPincode, setServices: setSelectedServices, setRadius }} services={services} tr={tr} /></section>}
      {activeTab === 'explorer' && <div className="grid single"><FacilityTable facilities={displayFacilities} selected={selected} setSelected={setSelected} onOpenTrust={openTrust} onOpenReview={openReview} language={language} tr={tr} /></div>}
      {activeTab === 'map' && <div className="grid single"><RadiusMap facilities={displayFacilities} selected={selected} setSelected={setSelected} radius={radius} setRadius={setRadius} onOpenTrust={openTrust} language={language} tr={tr} /></div>}
      {activeTab === 'verification' && <>
        <div className="trustReviewAccentLine" />
        <TrustReviewFacilityFilter selected={selected} facilities={displayFacilities} onSelectFacility={selectFacilityForReview} language={language} tr={tr} />
        <div className="grid trustReviewGrid">
          <div className="trustReviewColumn trustReviewLeftColumn"><SelectedFacilityPanel selected={selected} onOpenTrust={openTrust} onAddShortlist={addShortlist} onViewShortlists={() => setActiveTab('shortlists')} shortlistCount={shortlists.length + scenarioShortlists.length} userActionsCount={userActions.length} scenarioCount={scenarioShortlists.length} latestDate={latestInfoDate(facilityUpdates, selected || {})} language={language} tr={tr} /><RecentHistory title={tr('recentVerifications')} items={recentVerifications} empty={tr('noVerificationHistory')} language={language} tr={tr} /><FacilityInfoTimeline actions={facilityUpdates} facility={selected || {}} tr={tr} /></div>
          <div className="trustReviewColumn trustReviewRightColumn"><VerificationForm facility={selected} service={service} serviceLabel={serviceLabel} facilities={displayFacilities} location={city || state || country || 'India'} onVerified={onVerified} onHistory={refreshHistory} verification={trustVerification} verifying={trustVerifying} onVerifySources={verifyTrustSources} callResult={callResult} callingFacility={callingFacility} onCallFacility={callFacilityDemo} language={language} tr={tr} /><RecentHistory title={tr('recentUserActions')} items={userActions} empty={tr('noUserActions')} language={language} tr={tr} /><RecentHistory title={tr('savedScenarios')} items={scenarioShortlists} empty={tr('noSavedScenarios')} language={language} tr={tr} /></div>
        </div>
      </>}
      {activeTab === 'assistant'  && <><div className="trustReviewAccentLine chatAssistantAccentLine" /><div className="grid single assistantOnlyGrid"><AssistantPanel service={service} serviceLabel={serviceLabel} selected={selected} language={language} tr={tr} /></div></>}
      {activeTab === 'shortlists' && <div className="grid"><Shortlists selected={selected} shortlists={[...scenarioShortlists.map((x) => ({ ...x, name: x.title || x.location, meta: `${humanizeTerm(x.service)} • ${(x.facility_ids || []).length} facilities` })), ...shortlists]} onAdd={addShortlist} language={language} /><ServiceTable services={services} /></div>}
    </main>
    {trustOpen && <TrustCard facility={selected} serviceLabel={serviceLabel} verification={trustVerification} verifying={trustVerifying} onVerifySources={verifyTrustSources} onClose={() => setTrustOpen(false)} onMethodology={() => setMethodOpen(true)} language={language} tr={tr} />}
    {methodOpen && <MethodologyModal onClose={() => setMethodOpen(false)} />}
  </>;
}

createRoot(document.getElementById('root')).render(<App />);
