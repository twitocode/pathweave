export interface Plan {
	id: string;
	title: string;
	term: 'Fall 2026' | 'Winter 2027' | 'Spring/Summer 2027' | 'Unknown';
	createdAt: string;
	courseCount: number;
	userID: string;
}
