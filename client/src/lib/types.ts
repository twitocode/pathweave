export interface MeetingInfo {
	id: number;
	days: string;
	startTime: string | null;
	endTime: string | null;
	building: string;
	room: string;
  dayMask: number;
}

export interface TeacherInfo {
	id: number;
	name: string;
	avgRating: number | null;
	avgDifficulty: number | null;
	department: string;
	rmpId: string;
	numRatings: number;
}

export interface PlanCourse {
	id: string;
	courseId: number;
	code: string;
	name: string;
	description: string;
	restrictions: string;
	prerequisites: string[];
	units: number;
	types: string[];
	teachers: TeacherInfo[];
	sections: SectionInfo[];
}

export interface SectionInfo {
	id: number;
	name: string;
	type: string;
	term: string;
	mode: string;
	isInPerson: boolean;
	classNumber: number;
	meetings: MeetingInfo[];
	teachers: TeacherInfo[];
}

export interface Plan {
	id: string;
	title: string;
	term: TermNumber;
	createdAt: string;
	updatedAt?: string;
	courseCount?: number;
	userId?: string;
	courses?: PlanCourse[];
}

export type TermNumber = '2259' | '2261' | '2265' | '2269' | '2271' | '2275' | 'Unknown';
export type TermString =
	| 'Fall 2025'
	| 'Winter 2026'
	| 'Spring/Summer 2026'
	| 'Fall 2026'
	| 'Winter 2027'
	| 'Spring/Summer 2027'
	| 'Unknown';

export interface SectionMeeting {
	id: number;
	section: string;
	type: string;
	term: string;
	mode: string;
	isInPerson: boolean;
	classNumber: number;
	day: string;
	startTime: string;
	endTime: string;
	building: string;
	room: string;
	instructor: string;
	avgDifficulty: number;
	avgRating: number;
	parents: string[];
	dayMask?: number;
}

export interface GroupedSectionResults {
	sections: Record<string, SectionMeeting[]>;
	count: number;
	terms: TermNumber[];
}
