export interface MeetingInfo {
	id: number;
	days: string;
	startTime: string | null;
	endTime: string | null;
	building: string;
	room: string;
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
	userID?: string;
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

export interface Schedule {
	id: number;
	section: string;
	type: string;
	term: string;
	mode: string;
	is_in_person: boolean;
	class_number: number;
	day: string;
	start_time: string;
	end_time: string;
	building: string;
	room: string;
	instructor: string;
	avg_difficulty: number;
	avg_rating: number;
	parent: string;
}

export interface GroupedSectionResults {
	sections: Record<string, Schedule[]>;
	count: number;
	terms: TermNumber[];
}
